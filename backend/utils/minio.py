from minio import Minio
from minio.error import S3Error

BUCKET_NAME = "submission-uploads"
RUN_BUCKET = "run-bucket"
CONTAINER_BUCKET = "container-bucket"

minio_client = Minio(
    "minio:9000",
    access_key="admin",
    secret_key="password",
    secure=False,
)

def initialize_buckets(buckets: list[str]):
    try:
        for bucket in buckets:
            if not minio_client.bucket_exists(bucket):
                minio_client.make_bucket(bucket)
    except S3Error as e:
        print(f"Error initializing buckets: {e}")

initialize_buckets([BUCKET_NAME, RUN_BUCKET, CONTAINER_BUCKET])