from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.student import Student
from app.models.submission import Submission
from app.services.codeforces import cf_client


class SubmissionCollector:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def collect_for_student(self, student: Student, limit: int = 300) -> int:
        raw_submissions = await cf_client.get_user_submissions(student.cf_handle, count=limit)
        cpp_accepted = cf_client.filter_accepted_cpp(raw_submissions)

        existing = await self.db.execute(
            select(Submission.cf_submission_id).where(Submission.student_id == student.id)
        )
        existing_ids = {row[0] for row in existing.fetchall()}

        new_count = 0
        for sub in cpp_accepted:
            cf_id = sub["id"]
            if cf_id in existing_ids:
                continue

            contest_id = sub.get("contestId")
            if not contest_id:
                continue

            problem = sub.get("problem", {})
            submission = Submission(
                student_id=student.id,
                cf_submission_id=cf_id,
                problem_id=f"{contest_id}{problem.get('index', '')}",
                problem_name=problem.get("name", ""),
                language=sub.get("programmingLanguage", ""),
                verdict="OK",
                source_code="",
                submitted_at=datetime.fromtimestamp(sub.get("creationTimeSeconds", 0)),
            )
            self.db.add(submission)
            new_count += 1

        if new_count:
            await self.db.commit()
        return new_count

    async def collect_for_group(self, students: list[Student], limit: int = 300) -> dict:
        results = {}
        for student in students:
            try:
                count = await self.collect_for_student(student, limit)
                results[student.cf_handle] = {"status": "ok", "new_submissions": count}
            except Exception as e:
                results[student.cf_handle] = {"status": "error", "message": str(e)}
        return results
