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


def download_file(client: Minio, url: str, object_name: str):
    try:
        # Ensure the bucket exists
        if not client.bucket_exists(INTER_RUN_BUCKET):
            client.make_bucket(INTER_RUN_BUCKET)

        # Check if the file already exists
        try:
            client.stat_object(INTER_RUN_BUCKET, object_name)
            logger.info(
                f"{object_name} already exists in the bucket. Skipping download."
            )
            return
        except S3Error as e:
            if e.code != "NoSuchKey":
                raise

        with requests.get(url) as response:
            response.raise_for_status()  # Raise exception for HTTP errors
            with tempfile.NamedTemporaryFile(delete=True, dir="/tmp") as tmp_file:
                tmp_file.write(response.content)
                tmp_file.seek(0)
                client.put_object(
                    bucket_name=INTER_RUN_BUCKET,
                    object_name=object_name,
                    data=tmp_file,
                    length=len(response.content),
                    content_type=response.headers.get("content-type"),
                )

        logger.info(f"{object_name} successfully downloaded.")
    except S3Error as e:
        logger.error(f"MinIO error: {e}")
    except requests.RequestException as e:
        logger.error(f"HTTP request error: {e}")



def deconstruct_file(client: Minio, object_name: str):
    response = client.get_object(INTER_RUN_BUCKET, object_name)
    file_data = response.read()

    with tempfile.TemporaryDirectory(dir="/tmp") as input_dir, tempfile.TemporaryDirectory(dir="/tmp") as output_dir:
        input_file_path = os.path.join(input_dir, object_name)
        with open(input_file_path, "wb") as input_file:
            input_file.write(file_data)

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
                    INTER_RUN_BUCKET,
                    f"deconstruct/{file_name}",
                    data=output_file,
                    length=file_stat.st_size
                )


def prepare_benchmarks(client: Minio, url: str, object_name: str):
    download_file(client, url, object_name)
    deconstruct_file(client, object_name)


# def benchmark_image(tag: str):
