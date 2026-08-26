"""
Bulk import students from CSV.

Usage:
    python scripts/import_students.py students.csv
"""

import sys
import os
import csv
import asyncio
from pathlib import Path

BACKEND_DIR = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))
os.chdir(str(BACKEND_DIR))


async def import_csv(csv_path: str):
    from app.database import async_session, init_db
    from app.models.student import Student
    from app.models.group import Group
    from sqlalchemy import select

    await init_db()

    async with async_session() as db:
        # Get the first group (or create one)
        result = await db.execute(select(Group).limit(1))
        group = result.scalar_one_or_none()

        if not group:
            # Find the owner
            from app.models.user import User
            result = await db.execute(select(User).limit(1))
            user = result.scalar_one_or_none()
            if not user:
                print("No user found. Register via the web UI first.")
                return

            group = Group(name="CSE-2A 2026", owner_id=user.id)
            db.add(group)
            await db.commit()
            await db.refresh(group)
            print(f"Created group: {group.name}")

        # Get existing handles
        result = await db.execute(select(Student.cf_handle))
        existing = {row[0].lower() for row in result.fetchall()}

        # Read CSV
        with open(csv_path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            added = 0
            skipped = 0

            for row in reader:
                name = row["name"].strip()
                handle = row["cf_handle"].strip()

                if not name or not handle:
                    continue

                if handle.lower() in existing:
                    skipped += 1
                    continue

                student = Student(
                    group_id=group.id,
                    cf_handle=handle,
                    name=name,
                )
                db.add(student)
                existing.add(handle.lower())
                added += 1

            await db.commit()

        print(f"Done: {added} added, {skipped} already existed")
        print(f"Group: {group.name}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/import_students.py students.csv")
        sys.exit(1)

    csv_file = sys.argv[1]
    if not os.path.exists(csv_file):
        # Try relative to project root
        csv_file = str(Path(__file__).parent.parent / csv_file)

    if not os.path.exists(csv_file):
        print(f"File not found: {sys.argv[1]}")
        sys.exit(1)

    asyncio.run(import_csv(csv_file))
