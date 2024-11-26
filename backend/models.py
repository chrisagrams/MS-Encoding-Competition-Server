from pydantic import BaseModel, EmailStr
from typing import Optional


class SubmissionModel(BaseModel):
    email: EmailStr
    name: str
    submission_name: str
    file_key: str

    class Config:
        orm_mode = True
