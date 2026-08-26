from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Text, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import new_id


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    cf_submission_id: Mapped[int] = mapped_column(Integer, unique=True)
    problem_id: Mapped[str] = mapped_column(String(20))
    problem_name: Mapped[str] = mapped_column(String(255))
    language: Mapped[str] = mapped_column(String(50))
    verdict: Mapped[str] = mapped_column(String(50))
    source_code: Mapped[str] = mapped_column(Text)
    submitted_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="submissions")
    analysis = relationship("AnalysisResult", back_populates="submission", uselist=False, cascade="all, delete-orphan")
