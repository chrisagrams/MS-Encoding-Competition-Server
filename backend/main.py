from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Depends
from fastapi.responses import StreamingResponse
from minio import Minio
from io import BytesIO
import asyncio
import docker
import zipfile
import tarfile
import uuid
from sqlalchemy.orm import Session
from schema import Base, SessionLocal, engine, Submission
from models import SubmissionModel
from collections import defaultdict
from typing import Dict, Set
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from process import download_file
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

client = docker.from_env()

docker_client = docker.APIClient()

load_dotenv()

minio_client = Minio(
    "minio:9000",
    access_key="admin",
    secret_key="password",
    secure=False,
)

BUCKET_NAME = "submission-uploads"


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up the application...")
    try:
        # Minio bucket initialization
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)
            logger.info(f"Created bucket: {BUCKET_NAME}")
        else:
            logger.info(f"Bucket {BUCKET_NAME} already exists.")

        # Database initialization
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully.")

        # Download test file (if not exists)
        mzml_file = os.environ.get("TEST_MZML")
        mzml_file_url = os.environ.get("TEST_MZML_URL")
        logger.info(f"mzml_file: {mzml_file}")
        download_file(minio_client, url=mzml_file_url, object_name=mzml_file)

    except Exception as e:
        logger.error(f"An error occurred during startup: {e}")
        raise
    yield


app = FastAPI(lifespan=lifespan)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/hello-world")
def hello_world():
    return client.containers.run("hello-world")


@app.post("/upload")
async def upload(
    email: str = Form(...),
    name: str = Form(...),
    submissionName: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be zip archive.")

    file_key = str(uuid.uuid4())

    zip_data = await file.read()
    minio_client.put_object(
        BUCKET_NAME,
        file_key,
        BytesIO(zip_data),
        length=len(zip_data),
        content_type="application/zip",
    )

    new_submission = Submission(
        file_key=file_key,
        email=email,
        name=name,
        submission_name=submissionName,
    )

    db.add(new_submission)
    db.commit()
    db.refresh(new_submission)

    return {"file_key": file_key, "message": "File uploaded successfully"}


@app.post("/build-container/{file_key}")
async def build_container(file_key: str):
    response = minio_client.get_object(BUCKET_NAME, file_key)
    zip_data = BytesIO(response.read())  # Read in-memory
    response.close()
    response.release_conn()

    with zipfile.ZipFile(zip_data) as z:
        if not any(info.filename.startswith("transform/") for info in z.infolist()):
            # Check if transform directory is present
            raise HTTPException(
                status_code=400, detail="'transform' directory not found in zip."
            )

        # Create a tar archive for the "transform" directory
        tar_data = BytesIO()
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
            yield f"{success_message}\n"
            await asyncio.sleep(0)

        except docker.errors.BuildError as e:
            error_message = f"Docker build failed: {str(e)}"
            yield f"ERROR: {error_message}\n"
            raise HTTPException(status_code=500, detail=error_message)

    return StreamingResponse(log_stream(), media_type="text/plain")
