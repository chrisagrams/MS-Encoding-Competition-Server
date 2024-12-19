from fastapi import FastAPI
from models.schema import Base, engine
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from utils.minio import minio_client
from utils.database import init_db
from endpoints import upload, results, benchmark
from tasks import prepare_benchmarks
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up the application...")
    try:
        # Database initialization
        init_db()
        logger.info("Database tables created successfully.")

        # Download test file (if not exists)
        mzml_file = os.environ.get("TEST_MZML")
        mzml_file_url = os.environ.get("TEST_MZML_URL")
        logger.info(f"mzml_file: {mzml_file}")
        task = prepare_benchmarks.delay(url=mzml_file_url, object_name=mzml_file)
        logger.info(f"Initialization task ID: {task.id}")

    except Exception as e:
        logger.error(f"An error occurred during startup: {e}")
        raise
    yield


app = FastAPI(lifespan=lifespan, root_path="/api/")
app.include_router(upload.router)
app.include_router(results.router)
app.include_router(benchmark.router)



