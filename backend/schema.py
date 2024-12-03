from sqlalchemy import Column, String, Integer, Float, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

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

    test_results = relationship("TestResult", back_populates="submission")


class TestResult(Base):
    __tablename__ = "test_results"
    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(String, ForeignKey("submission.file_key"))
    encoding_runtime = Column(Float)
    decoding_runtime = Column(Float)
    ratio = Column(Float)
    accuracy = Column(Float)
    status = Column(String, nullable=False)

    submission = relationship("Submission", back_populates="test_results")
