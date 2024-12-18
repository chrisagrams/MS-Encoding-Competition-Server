from fastapi import FastAPI
from models.schema import Base, engine
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from process import prepare_benchmarks
from utils.minio import minio_client, BUCKET_NAME
from endpoints import upload, results, benchmark
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

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
        prepare_benchmarks(minio_client, url=mzml_file_url, object_name=mzml_file)

    except Exception as e:
        logger.error(f"An error occurred during startup: {e}")
        raise
    yield


app = FastAPI(lifespan=lifespan, root_path="/api/")
app.include_router(upload.router)
app.include_router(results.router)
app.include_router(benchmark.router)



