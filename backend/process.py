import docker
import logging
import requests
from io import BytesIO
from minio import Minio
from minio.error import S3Error
from tqdm import tqdm

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

        with requests.get(url, stream=True) as response:
            response.raise_for_status()  # Raise exception for HTTP errors
            total_size = int(response.headers.get("content-length", 0))

            buffer = BytesIO()

            with tqdm(
                total=total_size, unit="B", unit_scale=True, desc=object_name
            ) as pbar:
                for chunk in response.iter_content(
                    chunk_size=1024 * 1024
                ):  # 1MB chunks
                    buffer.write(chunk)
                    pbar.update(len(chunk))

            buffer.seek(0)

            client.put_object(
                bucket_name=INTER_RUN_BUCKET,
                object_name=object_name,
                data=buffer,
                length=total_size,
                content_type=response.headers.get("content-type"),
            )

        print(f"{object_name} successfully downloaded.")
    except S3Error as e:
        print(f"MinIO error: {e}")
    except requests.RequestException as e:
        print(f"HTTP request error: {e}")


# def prepare_benchmarks(client: Minio, test_file: str):


# def benchmark_image(tag: str):
