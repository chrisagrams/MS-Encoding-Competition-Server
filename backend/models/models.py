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
    status: str

    class Config:
        orm_mode = True
