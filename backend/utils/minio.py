from minio import Minio

BUCKET_NAME = "submission-uploads"

minio_client = Minio(
    "minio:9000",
    access_key="admin",
    secret_key="password",
    secure=False,
)