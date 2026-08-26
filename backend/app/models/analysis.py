from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Float, String
from sqlalchemy.types import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import new_id


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    submission_id: Mapped[str] = mapped_column(ForeignKey("submissions.id"), unique=True)
    student_id: Mapped[str] = mapped_column(ForeignKey("students.id"), index=True)
    anomaly_score: Mapped[float] = mapped_column(Float)
    ai_score: Mapped[float] = mapped_column(Float, default=0.0)
    feature_deviations: Mapped[dict] = mapped_column(JSON)
    cross_matches: Mapped[dict] = mapped_column(JSON, nullable=True)
    verdict: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    submission = relationship("Submission", back_populates="analysis")
