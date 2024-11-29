import docker
import logging
import requests
import tempfile
import os
import tarfile
import time
from io import BytesIO
from minio import Minio
from minio.error import S3Error

docker_client = docker.APIClient()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INTER_RUN_BUCKET = "inter-run-bucket"


def download_file(client: Minio, url: str, bucket:str, object_name: str):
    try:
        # Ensure the bucket exists
        if not client.bucket_exists(bucket):
            client.make_bucket(bucket)
            logger.info(f"{bucket} created.")

        # Check if the file already exists
        try:
            client.stat_object(bucket, object_name)
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
            with tempfile.NamedTemporaryFile(delete=True, dir="/tmp") as tmp_file:
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



def deconstruct_file(client: Minio, bucket: str, object_name: str):
    # Get mzML from bucket
    response = client.get_object(bucket, f"download/{object_name}")
    file_data = response.read()

    # Create two temporary directories, input and output
    with tempfile.TemporaryDirectory(dir="/tmp") as input_dir, tempfile.TemporaryDirectory(dir="/tmp") as output_dir:
        input_file_path = os.path.join(input_dir, object_name)
        with open(input_file_path, "wb") as input_file:
            input_file.write(file_data)

        # Configure and start container
        container = docker_client.create_container(
            image="chrisagrams/mzml-construct:latest",
            command="python -u deconstruct.py /input/test.mzML /output/ -f npy",
            host_config=docker_client.create_host_config(
                binds = {
                    input_dir: {'bind': '/input', 'mode': 'ro'},
                    output_dir: {'bind': '/output', 'mode': 'rw'}
                }
            )
        )

        docker_client.start(container=container.get('Id'))
        docker_client.wait(container=container.get('Id'))

        # Upload results to MinIO
        for file_name in os.listdir(output_dir):
            output_file_path = os.path.join(output_dir, file_name)
            with open(output_file_path, "rb") as output_file:
                file_stat = os.stat(output_file_path)
                client.put_object(
                    bucket,
                    f"deconstruct/{file_name}",
                    data=output_file,
                    length=file_stat.st_size
                )
                logger.info(f"Created deconstruct/{file_name}.")


def prepare_benchmarks(client: Minio, url: str, object_name: str):
    download_file(client, url, INTER_RUN_BUCKET, object_name)
    deconstruct_file(client, INTER_RUN_BUCKET, object_name)


# def benchmark_image(tag: str):
