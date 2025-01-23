from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO
from utils.minio import minio_client, BUCKET_NAME, CONTAINER_BUCKET
from minio.error import S3Error
from tasks import benchmark_image
from zipfile import ZipFile
import logging
import tarfile
import asyncio
import docker

docker_client = docker.APIClient()

router = APIRouter()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_transform_tar(zip_data: BytesIO) -> BytesIO:
    tar_data = BytesIO()
    with ZipFile(zip_data) as z:
        if not any(info.filename.startswith("transform/") for info in z.infolist()):
            # Check if transform directory is present
            return None

        # Create a tar archive for the "transform" directory
        with tarfile.open(fileobj=tar_data, mode="w") as tar:
            for file_info in z.infolist():
                if file_info.filename.startswith("transform/"):
                    file_bytes = z.read(file_info)
                    tar_info = tarfile.TarInfo(
                        name=file_info.filename[len("transform/") :]
                    )
                    tar_info.size = len(file_bytes)
                    tar.addfile(tar_info, BytesIO(file_bytes))
        tar_data.seek(0)
        return tar_data


def save_image_to_minio(image_name: str):
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


@router.post("/build-container/{file_key}")
async def build_container(file_key: str):
    response = minio_client.get_object(BUCKET_NAME, file_key)
    zip_data = BytesIO(response.read())  # Read in-memory
    response.close()
    response.release_conn()

    tar_data = create_transform_tar(zip_data)

    if tar_data is None:
        raise HTTPException(
            status_code=400, detail="Error in extracting uploaded zip."
        )

    async def log_stream():
        yield "Starting build...\n"
        await asyncio.sleep(0)  # Let the server send data to the client
        try:
            build_output = docker_client.build(
                fileobj=tar_data,
                custom_context=True,
                tag=f"transform-{file_key}:latest",
                decode=True,
            )

            for chunk in build_output:
                if "stream" in chunk:
                    log_message = chunk["stream"].strip()
                    yield f"{log_message}\n"
                    await asyncio.sleep(0)
                elif "error" in chunk:
                    error_message = chunk["error"].strip()
                    yield f"ERROR: {error_message}\n"
                    await asyncio.sleep(0)
                    raise HTTPException(status_code=500, detail=error_message)

            success_message = f"Docker image built successfully for {file_key}."
            save_image_to_minio(image_name=f"transform-{file_key}")
            yield f"{success_message}\n"
            await asyncio.sleep(0)

        except docker.errors.BuildError as e:
            error_message = f"Docker build failed: {str(e)}"
            yield f"ERROR: {error_message}\n"
            raise HTTPException(status_code=500, detail=error_message)

    return StreamingResponse(log_stream(), media_type="text/plain")


@router.post("/benchmark")
async def run_benchmark(image: str):
    task = benchmark_image.apply_async(args=[image])

    return {"task_id": task.id}