from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import new_id


class Student(Base):
    __tablename__ = "students"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    group_id: Mapped[str] = mapped_column(ForeignKey("groups.id"))
    cf_handle: Mapped[str] = mapped_column(String(100), index=True)
    name: Mapped[str] = mapped_column(String(255))
    joined_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    group = relationship("Group", back_populates="students")
    submissions = relationship("Submission", back_populates="student", cascade="all, delete-orphan")
    profile = relationship("StyleProfile", back_populates="student", uselist=False)
