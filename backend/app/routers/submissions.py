

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.group import Group
from app.models.student import Student
from app.models.submission import Submission
from app.models.user import User
from app.routers.auth import get_current_user
from app.services.collector import SubmissionCollector

router = APIRouter(prefix="/submissions", tags=["submissions"])


class CollectRequest(BaseModel):
    student_id: str
    limit: int = 300


class CollectGroupRequest(BaseModel):
    group_id: str
    limit: int = 200


class SubmissionResponse(BaseModel):
    id: str
    cf_submission_id: int
    problem_id: str
    problem_name: str
    language: str
    verdict: str
    submitted_at: str


@router.post("/collect")
async def collect_submissions(
    data: CollectRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Student).where(Student.id == data.student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    collector = SubmissionCollector(db)
    count = await collector.collect_for_student(student, data.limit)
    return {"status": "ok", "new_submissions": count, "handle": student.cf_handle}


@router.post("/collect-group")
async def collect_group_submissions(
    data: CollectGroupRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Group).where(Group.id == data.group_id, Group.owner_id == user.id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    result = await db.execute(select(Student).where(Student.group_id == group.id))
    students = result.scalars().all()

    collector = SubmissionCollector(db)
    results = await collector.collect_for_group(students, data.limit)
    return {"status": "ok", "results": results}


@router.get("/student/{student_id}", response_model=list[SubmissionResponse])
async def get_student_submissions(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Submission)
        .where(Submission.student_id == student_id)
        .order_by(Submission.submitted_at.desc())
        .limit(50)
    )
    submissions = result.scalars().all()
    return [
        SubmissionResponse(
            id=s.id,
            cf_submission_id=s.cf_submission_id,
            problem_id=s.problem_id,
            problem_name=s.problem_name,
            language=s.language,
            verdict=s.verdict,
            submitted_at=s.submitted_at.isoformat(),
        )
        for s in submissions
    ]


@router.get("/student/{student_id}/count")
async def get_submission_count(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(func.count()).select_from(Submission).where(Submission.student_id == student_id)
    )
    count = result.scalar()
    return {"count": count}


@router.get("/detail/{submission_id}")
async def get_submission_detail(
    submission_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.models.analysis import AnalysisResult

    result = await db.execute(select(Submission).where(Submission.id == submission_id))
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    result = await db.execute(select(Student).where(Student.id == submission.student_id))
    student = result.scalar_one_or_none()

    result = await db.execute(
        select(AnalysisResult).where(AnalysisResult.submission_id == submission.id)
    )
    analysis = result.scalar_one_or_none()

    response = {
        "id": submission.id,
        "cf_submission_id": submission.cf_submission_id,
        "problem_id": submission.problem_id,
        "problem_name": submission.problem_name,
        "language": submission.language,
        "verdict": submission.verdict,
        "source_code": submission.source_code,
        "submitted_at": submission.submitted_at.isoformat(),
        "student_name": student.name if student else None,
        "student_handle": student.cf_handle if student else None,
        "student_id": submission.student_id,
    }

    if analysis:
        response["analysis"] = {
            "anomaly_score": analysis.anomaly_score,
            "ai_score": analysis.ai_score,
            "verdict": analysis.verdict,
            "confidence": analysis.confidence,
            "feature_deviations": analysis.feature_deviations,
            "cross_matches": analysis.cross_matches,
        }

    return response
