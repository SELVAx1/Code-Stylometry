"""
Background monitor: polls Codeforces API for new submissions from all enrolled students.
When a new submission is detected:
  1. Stores metadata immediately
  2. Tries to fetch source code (public after contest ends)
  3. If source available + profile exists → auto-analyze
  4. If source not available → marks pending, retries on next cycle
"""

import asyncio
import logging
from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.student import Student
from app.models.submission import Submission
from app.models.profile import StyleProfile
from app.models.analysis import AnalysisResult
from app.services.codeforces import cf_client
from app.stylometry import FeatureExtractor, ProfileBuilder, AnomalyDetector
from app.stylometry.comparator import code_similarity

logger = logging.getLogger("monitor")

extractor = FeatureExtractor()
detector = AnomalyDetector()

POLL_INTERVAL = 300  # 5 minutes
BATCH_DELAY = 2  # seconds between CF API calls to avoid rate limit


class SubmissionMonitor:
    def __init__(self):
        self.running = False
        self.last_poll: datetime | None = None
        self.stats = {
            "total_polls": 0,
            "new_submissions": 0,
            "source_fetched": 0,
            "auto_analyzed": 0,
            "errors": 0,
        }
        self._task: asyncio.Task | None = None

    @property
    def status(self) -> dict:
        return {
            "running": self.running,
            "last_poll": self.last_poll.isoformat() if self.last_poll else None,
            "poll_interval_seconds": POLL_INTERVAL,
            **self.stats,
        }

    def start(self):
        if self.running:
            return
        self.running = True
        self._task = asyncio.create_task(self._poll_loop())
        logger.info("Monitor started (interval: %ds)", POLL_INTERVAL)

    def stop(self):
        self.running = False
        if self._task:
            self._task.cancel()
            self._task = None
        logger.info("Monitor stopped")

    async def _poll_loop(self):
        while self.running:
            try:
                await self.poll_all_students()
            except Exception as e:
                logger.error("Poll cycle error: %s", e)
                self.stats["errors"] += 1

            await asyncio.sleep(POLL_INTERVAL)

    async def poll_all_students(self):
        """One full poll cycle: check all students for new submissions."""
        self.stats["total_polls"] += 1
        self.last_poll = datetime.utcnow()

        async with async_session() as db:
            result = await db.execute(select(Student))
            students = result.scalars().all()

            for student in students:
                try:
                    await self._check_student(db, student)
                except Exception as e:
                    logger.warning("Error checking %s: %s", student.cf_handle, e)
                    self.stats["errors"] += 1

                await asyncio.sleep(BATCH_DELAY)

            # Retry pending submissions (no source code yet)
            await self._retry_pending(db)

    async def _check_student(self, db: AsyncSession, student: Student):
        """Check one student for new submissions via CF API."""
        raw = await cf_client.get_user_submissions(student.cf_handle, count=50)
        cpp_accepted = cf_client.filter_accepted_cpp(raw)

        if not cpp_accepted:
            return

        existing = await db.execute(
            select(Submission.cf_submission_id).where(
                Submission.student_id == student.id
            )
        )
        existing_ids = {row[0] for row in existing.fetchall()}

        new_subs = [s for s in cpp_accepted if s["id"] not in existing_ids]
        if not new_subs:
            return

        for sub in new_subs[:20]:  # cap per cycle
            cf_id = sub["id"]
            contest_id = sub.get("contestId", 0)
            problem = sub.get("problem", {})

            # Try to get source code from public page
            source_code = None
            if contest_id:
                try:
                    source_code = await cf_client.get_submission_source(contest_id, cf_id)
                    if source_code:
                        self.stats["source_fetched"] += 1
                except Exception:
                    pass
                await asyncio.sleep(1)

            submission = Submission(
                student_id=student.id,
                cf_submission_id=cf_id,
                problem_id=f"{contest_id}{problem.get('index', '')}",
                problem_name=problem.get("name", ""),
                language=sub.get("programmingLanguage", ""),
                verdict="OK",
                source_code=source_code or "",
                submitted_at=datetime.fromtimestamp(sub.get("creationTimeSeconds", 0)),
            )
            db.add(submission)
            self.stats["new_submissions"] += 1

        await db.commit()

        # Auto-analyze if we got source code and profile exists
        if source_code:
            await self._auto_analyze_new(db, student)

    async def _auto_analyze_new(self, db: AsyncSession, student: Student):
        """Auto-analyze unanalyzed submissions that have source code."""
        profile_result = await db.execute(
            select(StyleProfile).where(StyleProfile.student_id == student.id)
        )
        profile = profile_result.scalar_one_or_none()
        if not profile:
            return

        # Find submissions with source code but no analysis
        result = await db.execute(
            select(Submission)
            .outerjoin(AnalysisResult, AnalysisResult.submission_id == Submission.id)
            .where(
                Submission.student_id == student.id,
                Submission.source_code != "",
                AnalysisResult.id.is_(None),
            )
            .order_by(Submission.submitted_at.desc())
            .limit(10)
        )
        unanalyzed = result.scalars().all()

        # Get other students in same group for cross-comparison
        result = await db.execute(
            select(Student).where(
                Student.group_id == student.group_id,
                Student.id != student.id,
            )
        )
        other_students = result.scalars().all()

        for sub in unanalyzed:
            if len(sub.source_code.strip()) < 10:
                continue

            try:
                analysis = detector.analyze_submission(
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
                    anomaly_score=analysis["anomaly_score"],
                    ai_score=analysis.get("ai_score", 0.0),
                    feature_deviations=analysis["self_comparison"]["feature_deviations"],
                    cross_matches=cross_matches if cross_matches else None,
                    verdict=analysis["verdict"],
                    confidence=analysis["confidence"],
                )
                db.add(analysis_result)
                self.stats["auto_analyzed"] += 1
            except Exception as e:
                logger.warning("Auto-analyze failed for %s: %s", sub.cf_submission_id, e)

        await db.commit()

    async def _retry_pending(self, db: AsyncSession):
        """Retry fetching source for submissions that are still empty."""
        result = await db.execute(
            select(Submission)
            .where(Submission.source_code == "")
            .order_by(Submission.submitted_at.desc())
            .limit(50)
        )
        pending = result.scalars().all()

        if not pending:
            return

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
                    self.stats["source_fetched"] += 1
            except Exception:
                pass

            await asyncio.sleep(1.5)

        if fetched:
            await db.commit()
            logger.info("Retry: fetched source for %d pending submissions", fetched)

            # Auto-analyze newly fetched
            for sub in pending:
                if sub.source_code and len(sub.source_code.strip()) > 10:
                    student_result = await db.execute(
                        select(Student).where(Student.id == sub.student_id)
                    )
                    student = student_result.scalar_one_or_none()
                    if student:
                        await self._auto_analyze_new(db, student)

    async def force_poll(self):
        """Trigger an immediate poll cycle (called from API)."""
        await self.poll_all_students()


monitor = SubmissionMonitor()
