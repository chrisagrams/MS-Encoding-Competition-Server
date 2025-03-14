from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO
from utils.minio import minio_client, BUCKET_NAME, CONTAINER_BUCKET
from utils.docker import save_and_push_internal_image
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
                    relative_path = file_info.filename[len("transform/"):]
                    # Skip the __pycache__ folder and its contents
                    if relative_path.split("/")[0] == "__pycache__":
                        continue

                    file_bytes = z.read(file_info)
                    tar_info = tarfile.TarInfo(name=relative_path)
                    tar_info.size = len(file_bytes)
                    tar.addfile(tar_info, BytesIO(file_bytes))
        tar_data.seek(0)
        return tar_data


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
            save_and_push_internal_image(image_name=f"transform-{file_key}")
            yield f"{success_message}\n"
            await asyncio.sleep(0)

        except docker.errors.APIError as e:
            error_message = f"Docker build failed: {str(e)}"
            logger.error(error_message)
            yield f"ERROR: {error_message}\n"
            await asyncio.sleep(0)

    return StreamingResponse(log_stream(), media_type="text/plain")


@router.post("/benchmark")
async def run_benchmark(image: str):
    task = benchmark_image.apply_async(args=[image])

    return {"task_id": task.id}