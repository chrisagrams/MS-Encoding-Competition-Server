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

    # Start the container with a command that keeps it running
    container = docker_client.create_container(
        image="chrisagrams/mzml-construct:latest",
        command="sleep infinity",  # Keep the container running
    )

    container_id = container.get('Id')

    try:
        # Start the container
        docker_client.start(container=container_id)

        # Create /input and /output directories inside the container
        exec_create_cmd = docker_client.exec_create(
            container=container_id, cmd='mkdir -p /input /output')
        docker_client.exec_start(exec_create_cmd)

        # Copy the input file into the container's /input directory
        tar_stream = BytesIO()
        with tarfile.open(fileobj=tar_stream, mode='w') as tar:
            tarinfo = tarfile.TarInfo(name=object_name)
            tarinfo.size = len(file_data)
            tarinfo.mtime = time.time()
            tar.addfile(tarinfo, BytesIO(file_data))
        tar_stream.seek(0)
        success = docker_client.put_archive(
            container=container_id, path='/input', data=tar_stream)
        if not success:
            raise RuntimeError("Failed to copy input file into container")

        # Execute the processing command inside the container
        exec_cmd = f"python -u deconstruct.py /input/{object_name} /output/ -f npy"
        exec_create = docker_client.exec_create(
            container=container_id, cmd=exec_cmd)
        exec_output = docker_client.exec_start(exec_create, stream=True)
        for line in exec_output:
            print(line.decode('utf-8').rstrip())

        # Check exit code of the exec command
        exec_inspect = docker_client.exec_inspect(exec_create)
        if exec_inspect['ExitCode'] != 0:
            logs = docker_client.logs(
                container=container_id, stderr=True).decode("utf-8")
            raise RuntimeError(f"Container failed with logs:\n{logs}")

        # Retrieve the output files from /output directory in the container
        bits, stat = docker_client.get_archive(
            container=container_id, path='/output')
        file_like_object = BytesIO()
        for chunk in bits:
            file_like_object.write(chunk)
        file_like_object.seek(0)

        # Extract files from the tar archive and upload directly to MinIO
        with tarfile.open(fileobj=file_like_object, mode='r') as tar:
            for member in tar.getmembers():
                if member.isfile():
                    extracted_file = tar.extractfile(member)
                    file_data = extracted_file.read()
                    file_obj = BytesIO(file_data)
                    file_obj.seek(0)
                    minio_object_name = member.name.lstrip('/')
                    client.put_object(
                        INTER_RUN_BUCKET,
                        minio_object_name,
                        data=file_obj,
                        length=len(file_data)
                    )
    except Exception as e:
        raise RuntimeError(f"Error running deconstruct container: {e}")
    finally:
        # Clean up the container
        docker_client.remove_container(container=container_id, force=True)



def prepare_benchmarks(client: Minio, url: str, object_name: str):
    download_file(client, url, object_name)
    deconstruct_file(client, object_name)


# def benchmark_image(tag: str):
