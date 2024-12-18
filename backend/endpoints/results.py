from fastapi import APIRouter, Depends
from typing import List
from sqlalchemy.orm import Session
from models.models import ResultModel
from models.schema import Submission, TestResult
from utils.database import get_db

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