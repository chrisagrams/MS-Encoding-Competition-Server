from celery import Celery, chain
from kombu import Queue, Exchange
from process import *
from utils.minio import RUN_BUCKET
from utils.database import get_db

celery_app = Celery("tasks", broker="redis://redis", backend="redis://redis")

default_exchange = Exchange("default", type="direct")
submission_exchange = Exchange("submission", type="direct")

celery_app.conf.task_queues = (
    Queue("default", default_exchange, routing_key="default"),
    Queue("timed", submission_exchange, routing_key="submission.timed"),
)


@celery_app.task(queue="default")
def prepare_benchmarks(url: str, object_name: str):
    download_file(url, RUN_BUCKET, "init", object_name)
    deconstruct_file(RUN_BUCKET, "init", object_name)
    search_file(RUN_BUCKET, "init", object_name)


@celery_app.task(queue="timed")
def encode_benchmark_task(image: str, bucket: str, filename: str):
    db_session = next(get_db())
    encode_benchmark(image, bucket, filename, db_session)
    return image  # On success, return image name for next task


@celery_app.task(queue="default")
def post_encode_benchmark(image: str):
    db_session = next(get_db())
    reconstruct_submission(image)
    search_file(RUN_BUCKET, image, "new.mzML")
    delete_from_minio(RUN_BUCKET, image, "new.mzML")
    compare_results(image, db_session)
    update_database_entry(db_session, image, "status", "success")
    return image


@celery_app.task(queue="default")
def benchmark_image(image: str):
    db_session = next(get_db())
    update_database_entry(db_session, image, "status", "pending")

    task_chain = chain(
        encode_benchmark_task.s(image, RUN_BUCKET, "test.npy"),
        post_encode_benchmark.s(),
    )

    task_chain.apply_async()
