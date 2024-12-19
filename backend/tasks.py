from celery import Celery, chain
from process import download_file, deconstruct_file, search_file
from utils.minio import RUN_BUCKET

celery_app = Celery('tasks', broker='redis://redis', backend='redis://redis')


@celery_app.task
def prepare_benchmarks(url: str, object_name: str):
    download_file(url, RUN_BUCKET, "init", object_name)
    deconstruct_file(RUN_BUCKET, "init", object_name)
    search_file(RUN_BUCKET, "init", object_name)

 