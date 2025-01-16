import time
from statistics import mean
import docker
from docker.types import HostConfig
import logging
import requests
from tempfile import NamedTemporaryFile, TemporaryDirectory
import csv
import os
from pathlib import Path
import zipfile
from shutil import copy2
from minio import Minio
from minio.error import S3Error
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from models.schema import TestResult
from utils.docker import check_and_pull_image
from utils.minio import minio_client, RUN_BUCKET

docker_client = docker.APIClient()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def download_file(url: str, bucket: str, prefix: str, object_name: str):
    try:
        # Ensure the bucket exists
        if not minio_client.bucket_exists(bucket):
            minio_client.make_bucket(bucket)
            logger.info(f"{bucket} created.")

        # Check if the file already exists
        try:
            minio_client.stat_object(bucket, f"{prefix}/{object_name}")
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
                minio_client.put_object(
                    bucket_name=bucket,
                    object_name=f"{prefix}/{object_name}",
                    data=tmp_file,
                    length=len(response.content),
                    content_type=response.headers.get("content-type"),
                )

        logger.info(f"{object_name} successfully downloaded.")
    except S3Error as e:
        logger.error(f"MinIO error: {e}")
    except requests.RequestException as e:
        logger.error(f"HTTP request error: {e}")


def put_directory_to_minio(bucket: str, prefix: str, output_dir: str):
    for file_name in os.listdir(output_dir):
        output_file_path = os.path.join(output_dir, file_name)
        with open(output_file_path, "rb") as output_file:
            file_stat = os.stat(output_file_path)
            minio_client.put_object(
                bucket,
                f"{prefix}/{file_name}",
                data=output_file,
                length=file_stat.st_size,
            )
            logger.info(f"Created {prefix}/{file_name}.")


def deconstruct_file(bucket: str, prefix: str, object_name: str):
    # Check if deconstruct folder exists and if .xml and .npy files are present
    objects = list(minio_client.list_objects(bucket, prefix=f"{prefix}/deconstruct/"))
    xml_exists = any(obj.object_name.endswith(".xml") for obj in objects)
    npy_exists = any(obj.object_name.endswith(".npy") for obj in objects)
    if xml_exists and npy_exists:
        logger.info("Deconstruct already exists. Skipping deconstruct.")
        return

    # Get mzML from bucket
    response = minio_client.get_object(bucket, f"{prefix}/{object_name}")
    file_data = response.read()

    # Create two temporary directories, input and output
    with TemporaryDirectory(dir="/tmp") as input_dir, TemporaryDirectory(
        dir="/tmp"
    ) as output_dir:
        input_file_path = os.path.join(input_dir, object_name)
        with open(input_file_path, "wb") as input_file:
            input_file.write(file_data)

        # Configure and start container
        check_and_pull_image("chrisagrams/mzml-construct:latest")
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
        put_directory_to_minio(bucket, f"{prefix}/deconstruct", output_dir)


def search_file(bucket: str, prefix: str, object_name: str):
    # Check if search folder exists and if search files are present
    objects = list(minio_client.list_objects(bucket, prefix=f"{prefix}/search/"))
    pepxml_exists = any(obj.object_name.endswith(".pepXML") for obj in objects)
    pin_exists = any(obj.object_name.endswith(".pin") for obj in objects)
    tsv_exists = any(obj.object_name.endswith(".tsv") for obj in objects)
    if pepxml_exists and pin_exists and tsv_exists:
        logger.info("Search already exists. Skipping search.")
        return

    # Get mzML from bucket
    response = minio_client.get_object(bucket, f"{prefix}/{object_name}")
    file_data = response.read()

    # Create two temporary directories, input and output
    with TemporaryDirectory(dir="/tmp") as input_dir, TemporaryDirectory(
        dir="/tmp"
    ) as output_dir:
        input_file_path = os.path.join(input_dir, object_name)
        with open(input_file_path, "wb") as input_file:
            input_file.write(file_data)

        # Configure and start container
        check_and_pull_image("chrisagrams/msfragger:UP000005640")
        container = docker_client.create_container(
            image="chrisagrams/msfragger:UP000005640",
            entrypoint="/app/entrypoint.sh",
            command=f"/input/{object_name} /output",
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
        put_directory_to_minio(bucket, f"{prefix}/search", output_dir)


def update_database_entry(db_session, submission_id, field, value):
    """
    Utility function to update a specific field in the database.
    If the entry does not exist, it creates a new one.
    """
    try:
        test_result = (
            db_session.query(TestResult).filter_by(submission_id=submission_id).first()
        )
        if not test_result:
            test_result = TestResult(
                submission_id=submission_id,
                encoding_runtime=None,
                decoding_runtime=None,
                ratio=None,
                accuracy=None,
                status="pending",
            )
            db_session.add(test_result)
        setattr(test_result, field, value)
        db_session.commit()
        logger.info(f"Updated {field} for ID: {submission_id} with value: {value}")
    except SQLAlchemyError as e:
        db_session.rollback()
        logger.error(f"Failed to update {field} for ID {submission_id}: {str(e)}")


def eval_container(
    image: str, command: str, host_config: HostConfig, num_runs=5
) -> float:
    run_times = []
    for _ in range(num_runs):
        # Create container
        container = docker_client.create_container(
            image=image, command=command, host_config=host_config
        )

        container_id = container.get("Id")

        # Start timing
        start_time = time.time()

        docker_client.start(container=container_id)
        docker_client.wait(container=container_id)

        end_time = time.time()
        run_times.append(end_time - start_time)

        # Remove container after run
        docker_client.remove_container(container=container_id, force=True)

    # Calculate average execution time
    average_time = mean(run_times)
    return average_time


def compute_ratio(original_file: Path, compressed_file: Path) -> float:
    compression_ratio = float("nan")
    try:
        original_size = os.path.getsize(original_file)
        compressed_size = os.path.getsize(compressed_file)
        compression_ratio = (original_size - compressed_size) / original_size
    except OSError as e:
        logger.error(f"Error computing file sizes: {str(e)}")
    return compression_ratio


def encode_benchmark(
    image: str, src_bucket: str, object_name: str, db_session: Session
):
    # Get npy from bucket
    response = minio_client.get_object(src_bucket, f"init/deconstruct/{object_name}")
    file_data = response.read()

    # Create two temporary directories, input and output
    with TemporaryDirectory(dir="/tmp") as input_dir, TemporaryDirectory(
        dir="/tmp"
    ) as output_dir:
        input_file_path = os.path.join(input_dir, object_name)
        with open(input_file_path, "wb") as input_file:
            input_file.write(file_data)

        # Evaluate encode
        encoding_runtime = eval_container(
            image=f"transform-{image}",
            command="python -u main.py /input/test.npy /output/transformed.npy --mode=encode",
            host_config=docker_client.create_host_config(
                binds={
                    input_dir: {"bind": "/input", "mode": "ro"},
                    output_dir: {"bind": "/output", "mode": "rw"},
                }
            ),
        )

        # Update in DB
        update_database_entry(db_session, image, "encoding_runtime", encoding_runtime)

        # Copy transformed.npy to input_dir
        transformed_path = os.path.join(output_dir, "transformed.npy")
        if os.path.exists(transformed_path):
            copy2(transformed_path, input_dir)
        else:
            raise FileNotFoundError(
                f"{transformed_path} does not exist after encoding!"
            )

        # Decoding runtime
        decoding_runtime = eval_container(
            image=f"transform-{image}",
            command="python -u main.py /input/transformed.npy /output/new.npy --mode=decode",
            host_config=docker_client.create_host_config(
                binds={
                    input_dir: {"bind": "/input", "mode": "ro"},
                    output_dir: {"bind": "/output", "mode": "rw"},
                }
            ),
        )

        # Update in DB
        update_database_entry(db_session, image, "decoding_runtime", decoding_runtime)

        # Compute compression ratio
        original_file = os.path.join(input_dir, "test.npy")
        compressed_file = os.path.join(output_dir, "transformed.npy")
        compression_ratio = compute_ratio(original_file, compressed_file)

        # Update compression ratio in the database
        update_database_entry(db_session, image, "ratio", compression_ratio)

        # Put resulting .npy to submission run bucket
        new_npy = os.path.join(output_dir, "new.npy")
        with open(new_npy, "rb") as output_file:
            file_stat = os.stat(new_npy)
            minio_client.put_object(
                RUN_BUCKET,
                f"{image}/new.npy",
                data=output_file,
                length=file_stat.st_size,
            )


def reconstruct_submission(image: str):
    # Get npy from bucket
    response = minio_client.get_object(RUN_BUCKET, f"{image}/new.npy")
    npy_data = response.read()

    # Get XML from bucket
    response = minio_client.get_object(RUN_BUCKET, f"init/deconstruct/test.xml")
    xml_data = response.read()

    # Create two temporary directories, input and output
    with TemporaryDirectory(dir="/tmp") as input_dir, TemporaryDirectory(
        dir="/tmp"
    ) as output_dir:
        npy_file_path = os.path.join(input_dir, "new.npy")
        with open(npy_file_path, "wb") as input_file:
            input_file.write(npy_data)
        xml_file_path = os.path.join(input_dir, "test.xml")
        with open(xml_file_path, "wb") as input_file:
            input_file.write(xml_data)

        # Reconstruct mzML
        check_and_pull_image("chrisagrams/mzml-construct:latest")
        container = docker_client.create_container(
            image="chrisagrams/mzml-construct:latest",
            command="python -u construct.py /input/test.xml /input/new.npy /output/new.mzML",
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

        # Copy new.mzML to MinIO
        new_mzml_path = os.path.join(output_dir, "new.mzML")
        with open(new_mzml_path, "rb") as output_file:
            file_stat = os.stat(new_mzml_path)
            minio_client.put_object(
                RUN_BUCKET,
                f"{image}/new.mzML",
                data=output_file,
                length=file_stat.st_size,
            )

        # Delete new.npy from MinIO
        minio_client.remove_object(RUN_BUCKET, f"{image}/new.npy")


def extract_result_metrics(output_dir):
    results_path = os.path.join(output_dir, "results.csv")
    metrics = {}

    with open(results_path, mode="r") as csv_file:
        csv_reader = csv.DictReader(csv_file)

        for row in csv_reader:
            metrics[row["Metric"]] = float(row["Value"])

    return metrics


def compare_results(image: str, db_session: Session):
    # Get original pin file
    response = minio_client.get_object(RUN_BUCKET, f"init/search/test.pin")
    original_pin_data = response.read()

    # Get search pin file
    response = minio_client.get_object(RUN_BUCKET, f"{image}/search/new.pin")
    new_pin_data = response.read()

    with TemporaryDirectory(dir="/tmp") as input_dir, TemporaryDirectory(
        dir="/tmp"
    ) as output_dir:
        original_pin_path = os.path.join(input_dir, "test.pin")
        with open(original_pin_path, "wb") as input_file:
            input_file.write(original_pin_data)

        new_pin_path = os.path.join(input_dir, "new.pin")
        with open(new_pin_path, "wb") as input_file:
            input_file.write(new_pin_data)

        # Run compare container
        check_and_pull_image("chrisagrams/pats-compare:latest")
        container = docker_client.create_container(
            image="chrisagrams/pats-compare:latest",
            command="/input/test.pin /input/new.pin /output/",
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

        result_metrics = extract_result_metrics(output_dir)

        update_database_entry(db_session, image, "accuracy", result_metrics['Percent Preserved'])
        update_database_entry(db_session, image, 'peptide_percent_preserved', result_metrics['Percent Preserved'])
        update_database_entry(db_session, image, 'peptide_percent_missed', result_metrics['Percent Missed'])
        update_database_entry(db_session, image, 'peptide_percent_new', result_metrics['Percent New'])
