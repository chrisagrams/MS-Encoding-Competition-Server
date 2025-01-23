import docker
import logging
from io import BytesIO
from utils.minio import minio_client, CONTAINER_BUCKET
from minio.error import S3Error

docker_client = docker.APIClient()
logger = logging.getLogger(__name__)


def check_and_pull_image(image_name: str):
    try:
        docker_client.inspect_image(image_name)
    except docker.errors.ImageNotFound:
        docker_client.pull(image_name)


def save_and_push_internal_image(image_name: str):
    try:
        image_stream = docker_client.get_image(image_name)
        image_bytes = BytesIO()
        for chunk in image_stream:
            image_bytes.write(chunk)
        image_bytes.seek(0)

        minio_client.put_object(
            bucket_name=CONTAINER_BUCKET,
            object_name=f"{image_name}.tar",
            data=image_bytes,
            length=len(image_bytes.getvalue()),
            content_type="application/x-tar"
        )
    except S3Error as e:
        logger.error(f"MinIO error while saving Docker image: {e}")
    except docker.errors.DockerException as e:
        logger.error(f"Docker error while saving Docker image: {e}")
    except Exception as e:
        logger.error(f"Unexpected error while saving Docker image: {e}")


def check_and_pull_internal_image(image_name: str):
    try:
        docker_client.inspect_image(image_name)
    except docker.errors.ImageNotFound:
        try:
            response = minio_client.get_object(CONTAINER_BUCKET, f"{image_name}.tar")
            downloaded_image = BytesIO()
            for chunk in response.stream(32 * 1024):
                downloaded_image.write(chunk)
            downloaded_image.seek(0)
        except Exception as e:
            logging.error(f"Error downloading {image_name} from MinIO: {e}")
            return
        try: 
            docker_client.load_image(downloaded_image)
        except docker.errors.DockerException as e:
            logging.error(f"Error loading Docker image: {e}")
        finally:
            downloaded_image.close()
    except Exception as e:
        logging.error(f"Unexpected error occured pulling internal image: {e}")
        
        
def delete_docker_image(image_name: str):
    try:
        docker_client.remove_image(image=image_name, force=True)
    except docker.errors.ImageNotFound:
        logger.error(f"Docker image {image_name} not found.")
    except docker.errors.DockerException as e:
        logger.error(f"Failed to delete image {image_name}. {e}")
    except Exception as e:
        logger.error(f"Unexpected error occured deleting Docker image: {e}")