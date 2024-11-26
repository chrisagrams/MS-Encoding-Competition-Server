from sqlalchemy import Column, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:postgres@postgres:5432/submissions"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Submission(Base):
    __tablename__ = "submission"

    file_key = Column(String, primary_key=True, index=True)
    email = Column(String, nullable=False)
    name = Column(String, nullable=False)
    submission_name = Column(String, nullable=False)
