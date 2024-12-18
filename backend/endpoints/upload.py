from fastapi import APIRouter, File, Form, UploadFile, Depends, HTTPException
from sqlalchemy.orm import Session
from utils.database import get_db
from utils.minio import minio_client, BUCKET_NAME
from models.schema import Submission
import uuid
from io import BytesIO

router = APIRouter()

@router.post("/upload")
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