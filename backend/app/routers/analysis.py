

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.student import Student
from app.models.submission import Submission
from app.models.profile import StyleProfile
from app.models.analysis import AnalysisResult
from app.models.group import Group
from app.models.user import User
from app.routers.auth import get_current_user
from app.stylometry import FeatureExtractor, ProfileBuilder, AnomalyDetector
from app.stylometry.comparator import code_similarity

router = APIRouter(prefix="/analysis", tags=["analysis"])
extractor = FeatureExtractor()
profile_builder = ProfileBuilder()
detector = AnomalyDetector()


class BuildProfileRequest(BaseModel):
    student_id: str


class AnalyzeRequest(BaseModel):
    submission_id: str


class AnalyzeGroupRequest(BaseModel):
    group_id: str


@router.post("/build-profile")
async def build_profile(
    data: BuildProfileRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Student).where(Student.id == data.student_id))
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    result = await db.execute(
        select(Submission)
        .where(Submission.student_id == student.id)
        .order_by(Submission.submitted_at.asc())
    )
    submissions = result.scalars().all()

    if len(submissions) < 10:
        raise HTTPException(status_code=400, detail="Need at least 10 submissions to build profile")

    feature_vectors = extractor.extract_batch([s.source_code for s in submissions])
    profile_data = profile_builder.build_profile(feature_vectors)

    existing = await db.execute(
        select(StyleProfile).where(StyleProfile.student_id == student.id)
    )
    profile = existing.scalar_one_or_none()

    if profile:
        profile.profile_data = profile_data
        profile.submission_count = len(submissions)
    else:
        profile = StyleProfile(
            student_id=student.id,
            profile_data=profile_data,
            submission_count=len(submissions),
        )
        db.add(profile)

    await db.commit()
    return {
        "status": "ok",
        "student": student.cf_handle,
        "submission_count": len(submissions),
        "feature_count": len(profile_data),
    }


@router.post("/analyze-submission")
async def analyze_submission(
    data: AnalyzeRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Submission).where(Submission.id == data.submission_id))
    submission = result.scalar_one_or_none()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Get user profile
    result = await db.execute(
        select(StyleProfile).where(StyleProfile.student_id == submission.student_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=400, detail="No profile built for this student yet")

    # Get student info for cross-comparison
    result = await db.execute(select(Student).where(Student.id == submission.student_id))
    student = result.scalar_one_or_none()

    # Run analysis against own profile
    analysis = detector.analyze_submission(
        source_code=submission.source_code,
        user_profile=profile.profile_data,
    )

    # Cross-compare: find other students who solved the SAME problem and compare actual code
    cross_matches = []
    if student:
        result = await db.execute(
            select(Student).where(
                Student.group_id == student.group_id,
                Student.id != student.id,
            )
        )
        group_students = result.scalars().all()

        for gs in group_students:
            result = await db.execute(
                select(Submission).where(
                    Submission.student_id == gs.id,
                    Submission.problem_id == submission.problem_id,
                    Submission.source_code != "",
                ).order_by(Submission.submitted_at.desc())
                .limit(1)
            )
            their_submission = result.scalar_one_or_none()
            if not their_submission or not their_submission.source_code.strip():
                continue

            sim = code_similarity(submission.source_code, their_submission.source_code)
            if sim > 0.3:
                cross_matches.append({
                    "student_id": str(gs.id),
                    "student_name": gs.name,
                    "handle": gs.cf_handle,
                    "similarity": sim,
                    "problem_id": submission.problem_id,
                })

        cross_matches.sort(key=lambda x: x["similarity"], reverse=True)
        cross_matches = cross_matches[:5]

    if cross_matches:
        analysis["cross_matches"] = cross_matches

    # Save result
    analysis_result = AnalysisResult(
        submission_id=submission.id,
        student_id=submission.student_id,
        anomaly_score=analysis["anomaly_score"],
        ai_score=analysis.get("ai_score", 0.0),
        feature_deviations=analysis["self_comparison"]["feature_deviations"],
        cross_matches=analysis.get("cross_matches"),
        verdict=analysis["verdict"],
        confidence=analysis["confidence"],
    )
    db.add(analysis_result)
    await db.commit()

    return analysis


@router.get("/results/{student_id}")
async def get_student_results(
    student_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AnalysisResult, Submission)
        .join(Submission, AnalysisResult.submission_id == Submission.id)
        .where(AnalysisResult.student_id == student_id)
        .order_by(Submission.submitted_at.desc())
        .limit(50)
    )
    rows = result.all()
    return [
        {
            "id": str(r.id),
            "submission_id": str(r.submission_id),
            "anomaly_score": r.anomaly_score,
            "ai_score": r.ai_score,
            "verdict": r.verdict,
            "confidence": r.confidence,
            "problem_name": sub.problem_name,
            "submitted_at": sub.submitted_at.isoformat(),
            "created_at": r.created_at.isoformat(),
            "feature_deviations": r.feature_deviations,
            "cross_matches": r.cross_matches,
        }
        for r, sub in rows
    ]


@router.post("/build-all-profiles")
async def build_all_profiles(
    data: AnalyzeGroupRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Build profiles for all students in a group that have enough submissions."""
    result = await db.execute(select(Student).where(Student.group_id == data.group_id))
    students = result.scalars().all()

    built = []
    skipped = []
    for student in students:
        result = await db.execute(
            select(Submission)
            .where(
                Submission.student_id == student.id,
                Submission.source_code != "",
            )
            .order_by(Submission.submitted_at.asc())
        )
        submissions_list = result.scalars().all()

        valid = [s for s in submissions_list if len(s.source_code.strip()) > 10]
        if len(valid) < 10:
            skipped.append({"handle": student.cf_handle, "reason": f"only {len(valid)} valid submissions"})
            continue

        feature_vectors = extractor.extract_batch([s.source_code for s in valid])
        profile_data = profile_builder.build_profile(feature_vectors)

        existing = await db.execute(
            select(StyleProfile).where(StyleProfile.student_id == student.id)
        )
        profile = existing.scalar_one_or_none()
        if profile:
            profile.profile_data = profile_data
            profile.submission_count = len(valid)
        else:
            profile = StyleProfile(
                student_id=student.id,
                profile_data=profile_data,
                submission_count=len(valid),
            )
            db.add(profile)

        built.append({"handle": student.cf_handle, "submissions": len(valid)})

    await db.commit()
    return {"built": built, "skipped": skipped}


@router.post("/analyze-all")
async def analyze_all_submissions(
    data: AnalyzeGroupRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Analyze all unanalyzed submissions for students who have profiles."""
    result = await db.execute(select(Student).where(Student.group_id == data.group_id))
    students = result.scalars().all()

    total_analyzed = 0
    for student in students:
        profile_result = await db.execute(
            select(StyleProfile).where(StyleProfile.student_id == student.id)
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            continue

        result = await db.execute(
            select(Submission)
            .outerjoin(AnalysisResult, AnalysisResult.submission_id == Submission.id)
            .where(
                Submission.student_id == student.id,
                Submission.source_code != "",
                AnalysisResult.id.is_(None),
            )
        )
        unanalyzed = result.scalars().all()

        # Get other students in the group for cross-comparison
        other_students = [s for s in students if s.id != student.id]

        for sub in unanalyzed:
            if len(sub.source_code.strip()) < 10:
                continue

            try:
                analysis_data = detector.analyze_submission(
                    source_code=sub.source_code,
                    user_profile=profile.profile_data,
                )

                # Cross-compare: same problem, other students' actual code
                cross_matches = []
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
                    student_id=student.id,
                    anomaly_score=analysis_data["anomaly_score"],
                    ai_score=analysis_data.get("ai_score", 0.0),
                    feature_deviations=analysis_data["self_comparison"]["feature_deviations"],
                    cross_matches=cross_matches if cross_matches else None,
                    verdict=analysis_data["verdict"],
                    confidence=analysis_data["confidence"],
                )
                db.add(analysis_result)
                total_analyzed += 1
            except Exception:
                continue

        await db.commit()

    return {"total_analyzed": total_analyzed}


@router.get("/group-summary/{group_id}")
async def get_group_summary(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Student).where(Student.group_id == group_id))
    students = result.scalars().all()

    summary = []
    for student in students:
        result = await db.execute(
            select(AnalysisResult)
            .where(AnalysisResult.student_id == student.id)
            .order_by(AnalysisResult.created_at.desc())
            .limit(10)
        )
        results = result.scalars().all()

        anomalies = [r for r in results if r.anomaly_score > 0.6]
        summary.append({
            "student_id": str(student.id),
            "cf_handle": student.cf_handle,
            "name": student.name,
            "total_analyzed": len(results),
            "anomaly_count": len(anomalies),
            "avg_anomaly_score": sum(r.anomaly_score for r in results) / max(len(results), 1),
            "highest_anomaly": max((r.anomaly_score for r in results), default=0),
        })

    summary.sort(key=lambda x: x["anomaly_count"], reverse=True)
    return summary
