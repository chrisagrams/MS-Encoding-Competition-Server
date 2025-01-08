from fastapi import APIRouter, Depends, HTTPException
from typing import List
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from models.models import ResultModel
from models.schema import Submission, TestResult
from utils.database import get_db
from utils.minio import minio_client
from io import BytesIO
import zipfile

router = APIRouter()

@router.get("/results", response_model=List[ResultModel])
def get_all_results(db: Session = Depends(get_db)):
    results = db.query(TestResult).join(Submission).all()

    result_list = []
    for result in results:
        submission = result.submission
        result_list.append(
            ResultModel(
                submission_id=submission.file_key,
                name=submission.name,
                submission_name=submission.submission_name,
                encoding_runtime=result.encoding_runtime,
                decoding_runtime=result.decoding_runtime,
                ratio=result.ratio,
                accuracy=result.accuracy,
                status=result.status,
            )
        )

    return result_list


@router.get("/result", response_model=ResultModel)
def get_result(id: str, db: Session = Depends(get_db)):
    result = db.query(TestResult).join(Submission).filter(TestResult.submission_id == id).first()

    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    submission = result.submission
    return ResultModel(
        submission_id=submission.file_key,
        name=submission.name,
        submission_name=submission.submission_name,
        encoding_runtime=result.encoding_runtime,
        decoding_runtime=result.decoding_runtime,
        ratio=result.ratio,
        accuracy=result.accuracy,
        status=result.status,
        peptide_percent_preserved=result.peptide_percent_preserved,
        peptide_percent_missed=result.peptide_percent_missed,
        peptide_percent_new=result.peptide_percent_new,
    )

@router.get("/rank", response_model=dict) # TODO: Make a proper response model
def get_rank(id: str, db: Session = Depends(get_db)):
    result = db.query(TestResult).filter(TestResult.submission_id == id).first()

    if not result:
        raise HTTPException(status_code=404, detail="Result not found")
    
    encoding_runtime_rank = (
        db.query(func.count())
        .filter(TestResult.decoding_runtime < result.decoding_runtime)
        .scalar()
        + 1
    )

    decoding_runtime_rank = (
        db.query(func.count())
        .filter(TestResult.decoding_runtime < result.decoding_runtime)
        .scalar()
        + 1
    )

    ratio_rank = (
        db.query(func.count())
        .filter(TestResult.ratio > result.ratio)
        .scalar()
        + 1
    )

    accuracy_rank = (
        db.query(func.count())
        .filter(TestResult.accuracy > result.accuracy)
        .scalar()
        + 1
    )

    total_entries = db.query(func.count(TestResult.id)).scalar()

    return {
        "submission_id": id,
        "encoding_runtime_rank": encoding_runtime_rank,
        "decoding_runtime_rank": decoding_runtime_rank,
        "ratio_rank": ratio_rank,
        "accuracy_rank": accuracy_rank,
        "total_entries": total_entries, 
    }


@router.get("/submission-source")
def get_submission_source(id: str):
    try:
        response = minio_client.get_object("submission-uploads", id)
        zip_data = BytesIO(response.read())
        with zipfile.ZipFile(zip_data, 'r') as zip_file:
            encode_content = zip_file.read("transform/encode.py").decode('utf-8')
            decode_content = zip_file.read("transform/decode.py").decode('utf-8')
        
        return {
            "encode.py": encode_content,
            "decode.py": decode_content
        }
    except minio_client.exceptions.NoSuchKey:
        raise HTTPException(status_code=404, detail="File not found in MinIO bucket")
    except KeyError:
        raise HTTPException(status_code=400, detail="Required files are missing in the zip")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")