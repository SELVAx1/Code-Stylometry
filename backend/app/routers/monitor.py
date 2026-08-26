import asyncio

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.submission import Submission
from app.models.analysis import AnalysisResult
from app.models.student import Student
from app.models.user import User
from app.routers.auth import get_current_user
from pydantic import BaseModel

from app.services.monitor import monitor
from app.services.codeforces import cf_client

router = APIRouter(prefix="/monitor", tags=["monitor"])


class CFLoginRequest(BaseModel):
    handle_or_email: str
    password: str


@router.post("/cf-login")
async def cf_login(data: CFLoginRequest, user: User = Depends(get_current_user)):
    """Login to Codeforces with a real browser session — bypasses Cloudflare."""
    success = await cf_client.login(data.handle_or_email, data.password)
    if success:
        return {"status": "logged_in", "message": "CF session active — source code fetch enabled"}
    return {"status": "failed", "message": "Login failed — check credentials"}


@router.get("/cf-session")
async def cf_session_status(user: User = Depends(get_current_user)):
    return {"logged_in": cf_client.is_logged_in}


@router.get("/status")
async def get_monitor_status(user: User = Depends(get_current_user)):
    return monitor.status


@router.post("/start")
async def start_monitor(user: User = Depends(get_current_user)):
    monitor.start()
    return {"status": "started"}


@router.post("/stop")
async def stop_monitor(user: User = Depends(get_current_user)):
    monitor.stop()
    return {"status": "stopped"}


@router.post("/poll-now")
async def poll_now(user: User = Depends(get_current_user)):
    """Trigger an immediate poll cycle without waiting for the interval."""
    await monitor.force_poll()
    return {"status": "poll complete", **monitor.stats}


@router.post("/fetch-pending")
async def fetch_pending_source(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Retry fetching source code for all pending submissions, then auto-analyze."""
    if not cf_client.is_logged_in:
        raise HTTPException(status_code=400, detail="Connect to CF first")

    from app.models.profile import StyleProfile
    from app.stylometry import FeatureExtractor, AnomalyDetector
    from app.stylometry.comparator import code_similarity

    extractor = FeatureExtractor()
    detector = AnomalyDetector()

    result = await db.execute(
        select(Submission)
        .where(Submission.source_code == "")
        .order_by(Submission.submitted_at.desc())
        .limit(100)
    )
    pending = result.scalars().all()

    fetched = 0
    for sub in pending:
        contest_id = 0
        if sub.problem_id:
            digits = ""
            for ch in sub.problem_id:
                if ch.isdigit():
                    digits += ch
                else:
                    break
            contest_id = int(digits) if digits else 0
        if not contest_id:
            continue

        try:
            source = await cf_client.get_submission_source(contest_id, sub.cf_submission_id)
            if source and len(source.strip()) > 10:
                sub.source_code = source
                fetched += 1
        except Exception:
            pass

        await asyncio.sleep(1)

    if fetched:
        await db.commit()

    # Auto-analyze all submissions that now have source but no analysis
    analyzed = 0
    result = await db.execute(
        select(Submission)
        .outerjoin(AnalysisResult, AnalysisResult.submission_id == Submission.id)
        .where(
            Submission.source_code != "",
            AnalysisResult.id.is_(None),
        )
    )
    unanalyzed = result.scalars().all()

    for sub in unanalyzed:
        if len(sub.source_code.strip()) < 10:
            continue

        # Get student's profile
        profile_result = await db.execute(
            select(StyleProfile).where(StyleProfile.student_id == sub.student_id)
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            continue

        # Get student for group info
        student_result = await db.execute(
            select(Student).where(Student.id == sub.student_id)
        )
        student = student_result.scalar_one_or_none()
        if not student:
            continue

        try:
            analysis = detector.analyze_submission(
                source_code=sub.source_code,
                user_profile=profile.profile_data,
            )

            # Cross-compare: same problem, other students
            cross_matches = []
            other_result = await db.execute(
                select(Student).where(
                    Student.group_id == student.group_id,
                    Student.id != student.id,
                )
            )
            other_students = other_result.scalars().all()

            for other in other_students:
                other_sub_result = await db.execute(
                    select(Submission).where(
                        Submission.student_id == other.id,
                        Submission.problem_id == sub.problem_id,
                        Submission.source_code != "",
                    ).order_by(Submission.submitted_at.desc())
                    .limit(1)
                )
                other_sub = other_sub_result.scalar_one_or_none()
                if not other_sub or not other_sub.source_code.strip():
                    continue
                sim = code_similarity(sub.source_code, other_sub.source_code)
                if sim > 0.3:
                    cross_matches.append({
                        "student_id": str(other.id),
                        "student_name": other.name,
                        "handle": other.cf_handle,
                        "similarity": sim,
                        "problem_id": sub.problem_id,
                    })

            cross_matches.sort(key=lambda x: x["similarity"], reverse=True)
            cross_matches = cross_matches[:5]

            analysis_result = AnalysisResult(
                submission_id=sub.id,
                student_id=sub.student_id,
                anomaly_score=analysis["anomaly_score"],
                ai_score=analysis.get("ai_score", 0.0),
                feature_deviations=analysis["self_comparison"]["feature_deviations"],
                cross_matches=cross_matches if cross_matches else None,
                verdict=analysis["verdict"],
                confidence=analysis["confidence"],
            )
            db.add(analysis_result)
            analyzed += 1
        except Exception:
            continue

    if analyzed:
        await db.commit()

    return {"fetched": fetched, "analyzed": analyzed, "total_pending": len(pending)}


@router.get("/pending")
async def get_pending_submissions(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get submissions that are missing source code (pending fetch)."""
    result = await db.execute(
        select(Submission, Student)
        .join(Student, Submission.student_id == Student.id)
        .where(Submission.source_code == "")
        .order_by(Submission.submitted_at.desc())
        .limit(100)
    )
    rows = result.all()
    return [
        {
            "id": str(sub.id),
            "cf_submission_id": sub.cf_submission_id,
            "student_handle": student.cf_handle,
            "student_name": student.name,
            "problem_name": sub.problem_name,
            "submitted_at": sub.submitted_at.isoformat(),
        }
        for sub, student in rows
    ]


@router.get("/recent-alerts")
async def get_recent_alerts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get recent anomalous submissions (score > 0.5)."""
    result = await db.execute(
        select(AnalysisResult, Submission, Student)
        .join(Submission, AnalysisResult.submission_id == Submission.id)
        .join(Student, AnalysisResult.student_id == Student.id)
        .where(AnalysisResult.anomaly_score > 0.5)
        .order_by(AnalysisResult.created_at.desc())
        .limit(20)
    )
    rows = result.all()
    return [
        {
            "id": str(ar.id),
            "student_handle": student.cf_handle,
            "student_name": student.name,
            "problem_name": sub.problem_name,
            "anomaly_score": ar.anomaly_score,
            "verdict": ar.verdict,
            "confidence": ar.confidence,
            "submitted_at": sub.submitted_at.isoformat(),
            "analyzed_at": ar.created_at.isoformat(),
        }
        for ar, sub, student in rows
    ]


@router.get("/activity")
async def get_recent_activity(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get recent submission activity across all students."""
    result = await db.execute(
        select(Submission, Student)
        .join(Student, Submission.student_id == Student.id)
        .order_by(Submission.submitted_at.desc())
        .limit(30)
    )
    rows = result.all()

    # Also get analysis if exists
    activity = []
    for sub, student in rows:
        ar_result = await db.execute(
            select(AnalysisResult).where(AnalysisResult.submission_id == sub.id)
        )
        ar = ar_result.scalar_one_or_none()

        activity.append({
            "submission_id": str(sub.id),
            "cf_submission_id": sub.cf_submission_id,
            "student_handle": student.cf_handle,
            "student_name": student.name,
            "problem_name": sub.problem_name,
            "submitted_at": sub.submitted_at.isoformat(),
            "has_source": bool(sub.source_code and len(sub.source_code) > 10),
            "anomaly_score": ar.anomaly_score if ar else None,
            "verdict": ar.verdict if ar else None,
        })

    return activity
