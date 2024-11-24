from fastapi import FastAPI, File, UploadFile, HTTPException
from minio import Minio
from io import BytesIO
import docker
import zipfile

app = FastAPI()

client = docker.from_env()

minio_client = Minio(
    "minio:9000",
    access_key="admin",
    secret_key="password", 
    secure=False,
)


BUCKET_NAME = "submission-uploads"
if not minio_client.bucket_exists(BUCKET_NAME):
    minio_client.make_bucket(BUCKET_NAME)


@app.get("/hello-world")
def hello_world():
    return client.containers.run("hello-world")

@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="File must be zip archive.")

    zip_data = await file.read()
    minio_client.put_object(
        BUCKET_NAME, file.filename, BytesIO(zip_data), length=len(zip_data)
    )

    return {"filename": file.filename, "message": "File uploaded successfully"}



