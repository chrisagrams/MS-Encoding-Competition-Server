from pydantic import BaseModel, EmailStr
from typing import Optional


class SubmissionModel(BaseModel):
    email: EmailStr
    name: str
    submission_name: str
    file_key: str

    class Config:
        orm_mode = True


class TestResultModel(BaseModel):
    result_id: int
    runtime: float
    ratio: float
    status: str

    class Config:
        orm_mode = True


# Used in client
class ResultModel(BaseModel):
    submission_id: str
    name: str
    submission_name: str
    encoding_runtime: Optional[float] = None
    decoding_runtime: Optional[float] = None
    ratio: Optional[float] = None
    accuracy: Optional[float] = None
    peptide_percent_preserved: Optional[float] = None
    peptide_percent_missed: Optional[float] = None
    peptide_percent_new: Optional[float] = None
    status: str

    class Config:
        orm_mode = True


class RankModel(BaseModel):
    submission_id: str
    encoding_runtime_rank: Optional[int]
    decoding_runtime_rank: Optional[int]
    ratio_rank: Optional[int]
    accuracy_rank: Optional[int]
    total_entries: int