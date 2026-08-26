"""
Reset bad data: removes N/A submissions from DB and disk so you can re-collect properly.

Usage:
    python scripts/reset_data.py
"""

import sys
import os
import asyncio
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(str(BACKEND_DIR))

SUBMISSIONS_DIR = Path(__file__).parent.parent / "data" / "submissions"


def clean_disk():
    """Remove .cpp files that contain N/A or are too short."""
    removed = 0
    for handle_dir in SUBMISSIONS_DIR.iterdir():
        if not handle_dir.is_dir():
            continue
        for cpp_file in handle_dir.glob("*.cpp"):
            content = cpp_file.read_text(encoding="utf-8").strip()
            if content in ("N/A", "") or len(content) < 10:
                cpp_file.unlink()
                json_file = handle_dir / f"{cpp_file.stem}.json"
                if json_file.exists():
                    json_file.unlink()
                removed += 1
    print(f"Removed {removed} bad files from disk.")


async def clean_db():
    """Remove submissions with N/A source code and related analysis results."""
    from app.database import async_session, init_db
    from app.models.submission import Submission
    from app.models.analysis import AnalysisResult
    from app.models.profile import StyleProfile
    from sqlalchemy import select, delete

    await init_db()

    async with async_session() as db:
        # Find bad submissions
        result = await db.execute(select(Submission))
        all_subs = result.scalars().all()

        bad_ids = []
        for sub in all_subs:
            if not sub.source_code or sub.source_code.strip() in ("N/A", "") or len(sub.source_code.strip()) < 10:
                bad_ids.append(sub.id)

        if bad_ids:
            # Delete analysis results for bad submissions
            await db.execute(
                delete(AnalysisResult).where(AnalysisResult.submission_id.in_(bad_ids))
            )
            # Delete bad submissions
            await db.execute(
                delete(Submission).where(Submission.id.in_(bad_ids))
            )
            await db.commit()
            print(f"Removed {len(bad_ids)} bad submissions from database.")
        else:
            print("No bad submissions in database.")

        # Delete all profiles (will rebuild from clean data)
        result = await db.execute(delete(StyleProfile))
        await db.commit()
        print(f"Cleared {result.rowcount} style profiles (rebuild after re-import).")


if __name__ == "__main__":
    print("Cleaning up bad data...\n")
    clean_disk()
    asyncio.run(clean_db())
    print("\nDone! Next steps:")
    print("  1. Run: python scripts/cf_scraper.py")
    print("     (Each student logs into their own CF account)")
    print("  2. Run: python scripts/cf_scraper.py import")
    print("  3. Build profiles and analyze via the web UI")
