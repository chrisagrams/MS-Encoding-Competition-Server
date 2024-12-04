import time
from statistics import mean
import docker
import logging
import requests
from tempfile import NamedTemporaryFile, TemporaryDirectory
import os
from pathlib import Path
import zipfile
from minio import Minio
from minio.error import S3Error
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from schema import TestResult

docker_client = docker.APIClient()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INTER_RUN_BUCKET = "inter-run-bucket"

def download_file(client: Minio, url: str, bucket: str, object_name: str):
    try:
        # Ensure the bucket exists
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            logger.info(f"{bucket} created.")

        # Check if the file already exists
        try:
            client.stat_object(bucket, f"download/{object_name}")
            logger.info(
                f"{object_name} already exists in the bucket. Skipping download."
            )
            return
        except S3Error as e:
            if e.code != "NoSuchKey":
                raise

        # Download URL and put into bucket
        with requests.get(url) as response:
            response.raise_for_status()  # Raise exception for HTTP errors
            with NamedTemporaryFile(delete=True, dir="/tmp") as tmp_file:
                tmp_file.write(response.content)
                tmp_file.seek(0)
                client.put_object(
                    bucket_name=bucket,
                    object_name=f"download/{object_name}",
                    data=tmp_file,
                    length=len(response.content),
                    content_type=response.headers.get("content-type"),
                )

        logger.info(f"{object_name} successfully downloaded.")
    except S3Error as e:
        logger.error(f"MinIO error: {e}")
    except requests.RequestException as e:
        logger.error(f"HTTP request error: {e}")


def put_directory_to_minio(client: Minio, bucket: str, prefix: str, output_dir: str):
    for file_name in os.listdir(output_dir):
        output_file_path = os.path.join(output_dir, file_name)
        with open(output_file_path, "rb") as output_file:
            file_stat = os.stat(output_file_path)
            client.put_object(
                bucket,
                f"{prefix}/{file_name}",
                data=output_file,
                length=file_stat.st_size,
            )
            logger.info(f"Created {prefix}/{file_name}.")


def deconstruct_file(client: Minio, bucket: str, object_name: str):
    # Check if deconstruct folder exists and if .xml and .npy files are present
    objects = list(client.list_objects(bucket, prefix="deconstruct/"))
    xml_exists = any(obj.object_name.endswith(".xml") for obj in objects)
    npy_exists = any(obj.object_name.endswith(".npy") for obj in objects)
    if xml_exists and npy_exists:
        logger.info("Deconstruct already exists. Skipping deconstruct.")
        return

    # Get mzML from bucket
    response = client.get_object(bucket, f"download/{object_name}")
    file_data = response.read()

    # Create two temporary directories, input and output
    with TemporaryDirectory(dir="/tmp") as input_dir, TemporaryDirectory(
        dir="/tmp"
    ) as output_dir:
        input_file_path = os.path.join(input_dir, object_name)
        with open(input_file_path, "wb") as input_file:
            input_file.write(file_data)

        # Configure and start container
        container = docker_client.create_container(
            image="chrisagrams/mzml-construct:latest",
            command="python -u deconstruct.py /input/test.mzML /output/ -f npy",
            host_config=docker_client.create_host_config(
                binds={
                    input_dir: {"bind": "/input", "mode": "ro"},
                    output_dir: {"bind": "/output", "mode": "rw"},
                }
            ),
        )

        container_id = container.get("Id")

        docker_client.start(container=container_id)
        docker_client.wait(container=container_id)
        docker_client.remove_container(container=container_id)

        # Upload results to MinIO
        put_directory_to_minio(client, bucket, "deconstruct", output_dir)


def search_file(client: Minio, bucket: str, object_name: str):
    # Check if search folder exists and if search files are present
    objects = list(client.list_objects(bucket, prefix="search/"))
    pepxml_exists = any(obj.object_name.endswith(".pepXML") for obj in objects)
    pin_exists = any(obj.object_name.endswith(".pin") for obj in objects)
    tsv_exists = any(obj.object_name.endswith(".tsv") for obj in objects)
    if pepxml_exists and pin_exists and tsv_exists:
        logger.info("Search already exists. Skipping search.")
        return

    # Get mzML from bucket
    response = client.get_object(bucket, f"download/{object_name}")
    file_data = response.read()

    # Create two temporary directories, input and output
    with TemporaryDirectory(dir="/tmp") as input_dir, TemporaryDirectory(
        dir="/tmp"
    ) as output_dir:
        input_file_path = os.path.join(input_dir, object_name)
        with open(input_file_path, "wb") as input_file:
            input_file.write(file_data)

        # Configure and start container
        container = docker_client.create_container(
            image="chrisagrams/msfragger:UP000005640",
            entrypoint="/app/entrypoint.sh",
            command="/input/test.mzML /output",
            host_config=docker_client.create_host_config(
                binds={
                    input_dir: {"bind": "/input", "mode": "ro"},
                    output_dir: {"bind": "/output", "mode": "rw"},
                }
            ),
        )

        container_id = container.get("Id")

        docker_client.start(container=container_id)
        docker_client.wait(container=container_id)
        docker_client.remove_container(container=container_id)

        # Unzip the output ZIP file
        for file_name in os.listdir(output_dir):
            if file_name.endswith(".zip"):
                zip_path = os.path.join(output_dir, file_name)
                with zipfile.ZipFile(zip_path, "r") as zip_ref:
                    zip_ref.extractall(output_dir)
                os.remove(zip_path)

        # Upload results to MinIO
        put_directory_to_minio(client, bucket, "search", output_dir)


def prepare_benchmarks(client: Minio, url: str, object_name: str):
    download_file(client, url, INTER_RUN_BUCKET, object_name)
    deconstruct_file(client, INTER_RUN_BUCKET, object_name)
    search_file(client, INTER_RUN_BUCKET, object_name)


def update_database_entry(db_session, submission_id, field, value):
    """
    Utility function to update a specific field in the database.
    If the entry does not exist, it creates a new one.
    """
    try:
        test_result = db_session.query(TestResult).filter_by(submission_id=submission_id).first()
        if not test_result:
            test_result = TestResult(
                submission_id=submission_id,
                encoding_runtime=None,
                decoding_runtime=None,
                ratio=None,
                accuracy=None,
                status="pending"
            )
            db_session.add(test_result)
        setattr(test_result, field, value)
        db_session.commit()
        logger.info(f"Updated {field} for ID: {submission_id} with value: {value}")
    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error(f"Failed to update {field} for ID {submission_id}: {str(e)}")


def compute_ratio(original_file: Path, compressed_file: Path) -> float:
    compression_ratio = float('nan')
    try: 
        original_size = os.path.getsize(original_file)
        compressed_size = os.path.getsize(compressed_file)
        compression_ratio = (original_size - compressed_size) / original_size
    except OSError as e:
        logger.error(f"Error computing file sizes: {str(e)}")
    return compression_ratio


def encode_benchmark(client: Minio, image: str, src_bucket: str, object_name: str, db_session: Session):
    # Get npy from bucket
    response = client.get_object(src_bucket, f"deconstruct/{object_name}")
    file_data = response.read()

    # Create two temporary directories, input and output
    with TemporaryDirectory(dir="/tmp") as input_dir, TemporaryDirectory(dir="/tmp") as output_dir:
        input_file_path = os.path.join(input_dir, object_name)
        with open(input_file_path, "wb") as input_file:
            input_file.write(file_data)

        # Prepare benchmark runs
        run_times = []
        for _ in range(5):  # Run the container 5 times
            # Configure container
            container = docker_client.create_container(
                image=f"transform-{image}",
                command="python -u main.py /input/test.npy /output/transformed.npy --mode=encode",
                host_config=docker_client.create_host_config(
                    binds={
                        input_dir: {"bind": "/input", "mode": "ro"},
                        output_dir: {"bind": "/output", "mode": "rw"},
                    }
                ),
            )

            container_id = container.get("Id")

            # Start timing
            start_time = time.time()

            docker_client.start(container=container_id)
            docker_client.wait(container=container_id)

            end_time = time.time()
            run_times.append(end_time - start_time)

            logger.info(f"Encoding runtime: {(end_time-start_time):.2f}")
            
            # Remove container after run
            docker_client.remove_container(container=container_id, force=True)

        # Calculate average execution time
        average_time = mean(run_times)
        logger.info(f"Average encode execution time over 5 runs: {average_time:.2f} seconds")

        # Update in DB
        update_database_entry(db_session, image, "encoding_runtime", average_time)

        run_times = []
        for _ in range(5): # Run the container 5 times
            # Configure contaienr
            container = docker_client.create_container(
                image=f"transform-{image}",
                command="python -u main.py /input/transformed.npy /output/new.npy --mode=decode",
                host_config=docker_client.create_host_config(
                    binds={
                        output_dir: {"bind": "/input", "mode": "ro"}, # Bind the output from last container as input
                        output_dir: {"bind": "/output", "mode": "rw"},
                    }
                ),
            )

            container_id = container.get("Id")

            # Start timing
            start_time = time.time()

            docker_client.start(container=container_id)
            docker_client.wait(container=container_id)

            end_time = time.time()
            run_times.append(end_time - start_time)

            logger.info(f"Decoding runtime: {(end_time-start_time):.2f}")
            
            # Remove container after run
            docker_client.remove_container(container=container_id, force=True)
        
        # Calculate average execution time
        average_time = mean(run_times)
        logger.info(f"Average encode execution time over 5 runs: {average_time:.2f} seconds")

        # Update in DB
        update_database_entry(db_session, image, "decoding_runtime", average_time)

        # Compute compression ratio
        compression_ratio = compute_ratio(
            original_file=os.path.join(input_dir, "test.npy"),
            compressed_file=os.path.join(output_dir, "transformed.npy")
        )

        # Update compression ratio in the database
        update_database_entry(db_session, image, "ratio", compression_ratio)


def benchmark_image(client: Minio, image: str, db_session: Session):
    update_database_entry(db_session, image, "status", "pending")
    encode_benchmark(client, image, INTER_RUN_BUCKET, "test.npy", db_session)
    update_database_entry(db_session, image, "status", "success")