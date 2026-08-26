import asyncio
import json
from datetime import datetime
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.student import Student
from app.models.submission import Submission
from app.services.codeforces import cf_client

SUBMISSIONS_DIR = Path(__file__).parent.parent.parent.parent / "data" / "submissions"


class SubmissionCollector:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def collect_for_student(self, student: Student, limit: int = 300) -> int:
        # First try to import from local files (collected by cf_scraper.py)
        local_count = await self._import_from_files(student)
        if local_count > 0:
            return local_count

        # Fallback: try CF API for metadata only (no source code)
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

            # Try to get source from local files
            source_code = self._read_local_source(student.cf_handle, cf_id)
            if not source_code:
                continue

            problem = sub.get("problem", {})
            submission = Submission(
                student_id=student.id,
                cf_submission_id=cf_id,
                problem_id=f"{contest_id}{problem.get('index', '')}",
                problem_name=problem.get("name", ""),
                language=sub.get("programmingLanguage", ""),
                verdict="OK",
                source_code=source_code,
                submitted_at=datetime.fromtimestamp(sub.get("creationTimeSeconds", 0)),
            )
            self.db.add(submission)
            new_count += 1

        if new_count:
            await self.db.commit()
        return new_count

    async def _import_from_files(self, student: Student) -> int:
        """Import submissions from files collected by cf_scraper.py."""
        handle_dir = SUBMISSIONS_DIR / student.cf_handle
        if not handle_dir.exists():
            return 0

        existing = await self.db.execute(
            select(Submission.cf_submission_id).where(Submission.student_id == student.id)
        )
        existing_ids = {row[0] for row in existing.fetchall()}

        cpp_files = sorted(handle_dir.glob("*.cpp"))
        new_count = 0
        for cpp_file in cpp_files:
            if not cpp_file.stem.isdigit():
                continue
            sub_id = int(cpp_file.stem)
            if sub_id in existing_ids:
                continue

            meta_file = handle_dir / f"{sub_id}.json"
            if not meta_file.exists():
                continue

            source_code = cpp_file.read_text(encoding="utf-8")
            meta = json.loads(meta_file.read_text())

            submission = Submission(
                student_id=student.id,
                cf_submission_id=sub_id,
                problem_id=meta.get("problemId", ""),
                problem_name=meta.get("problemName", ""),
                language=meta.get("language", ""),
                verdict="OK",
                source_code=source_code,
                submitted_at=datetime.fromtimestamp(meta.get("creationTime", 0)),
            )
            self.db.add(submission)
            new_count += 1

        if new_count:
            await self.db.commit()
        return new_count

    def _read_local_source(self, handle: str, submission_id: int) -> str | None:
        """Read source code from local file if available."""
        filepath = SUBMISSIONS_DIR / handle / f"{submission_id}.cpp"
        if filepath.exists():
            return filepath.read_text(encoding="utf-8")
        return None

    async def collect_for_group(self, students: list[Student], limit: int = 300) -> dict:
        results = {}
        for student in students:
            try:
                count = await self.collect_for_student(student, limit)
                results[student.cf_handle] = {"status": "ok", "new_submissions": count}
            except Exception as e:
                results[student.cf_handle] = {"status": "error", "message": str(e)}
        return results
