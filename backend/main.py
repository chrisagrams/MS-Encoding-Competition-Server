from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Depends
from minio import Minio
from io import BytesIO
import docker
import zipfile
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
        BUCKET_NAME, file_key, BytesIO(zip_data), length=len(zip_data)
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



