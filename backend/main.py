import docker.errors
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Depends
from minio import Minio
from io import BytesIO
import docker
import zipfile
import tarfile
import uuid
from sqlalchemy.orm import Session
from schema import Base, SessionLocal, engine, Submission
from models import SubmissionModel

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

Base.metadata.create_all(bind=engine)


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
        print(z.infolist())
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

    # Try to build Docker image
    try:
        image, logs = client.images.build(
            fileobj=tar_data,
            custom_context=True,
            tag=f"transform-{file_key}:latest",
        )
        for log in logs:
            print(log)  # TODO: Set up a websocket to emmit this to client
    except docker.errors.BuildError as e:
        raise HTTPException(status_code=500, detail=f"Docker build failed: {str(e)}")

    return {"message": "Docker image built successfully", "image_id": image.id}
