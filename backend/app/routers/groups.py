import secrets


from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.group import Group
from app.models.student import Student
from app.models.user import User
from app.routers.auth import get_current_user

router = APIRouter(prefix="/groups", tags=["groups"])


class GroupCreate(BaseModel):
    name: str


class StudentAdd(BaseModel):
    cf_handle: str
    name: str


class GroupResponse(BaseModel):
    id: str
    name: str
    code: str
    student_count: int


class StudentResponse(BaseModel):
    id: str
    cf_handle: str
    name: str


@router.post("/", response_model=GroupResponse)
async def create_group(
    data: GroupCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    code = secrets.token_hex(4).upper()
    group = Group(name=data.name, code=code, owner_id=user.id)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return GroupResponse(id=group.id, name=group.name, code=group.code, student_count=0)


@router.get("/", response_model=list[GroupResponse])
async def list_groups(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Group).where(Group.owner_id == user.id).options(selectinload(Group.students))
    )
    groups = result.scalars().all()
    return [
        GroupResponse(id=g.id, name=g.name, code=g.code, student_count=len(g.students))
        for g in groups
    ]


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Group).where(Group.id == group_id, Group.owner_id == user.id)
        .options(selectinload(Group.students))
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return GroupResponse(id=group.id, name=group.name, code=group.code, student_count=len(group.students))


@router.post("/{group_id}/students", response_model=StudentResponse)
async def add_student(
    group_id: str,
    data: StudentAdd,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Group).where(Group.id == group_id, Group.owner_id == user.id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    student = Student(group_id=group.id, cf_handle=data.cf_handle, name=data.name)
    db.add(student)
    await db.commit()
    await db.refresh(student)
    return StudentResponse(id=student.id, cf_handle=student.cf_handle, name=student.name)


@router.get("/{group_id}/students", response_model=list[StudentResponse])
async def list_students(
    group_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Group).where(Group.id == group_id, Group.owner_id == user.id)
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Group not found")

    result = await db.execute(select(Student).where(Student.group_id == group_id))
    students = result.scalars().all()
    return [StudentResponse(id=s.id, cf_handle=s.cf_handle, name=s.name) for s in students]


@router.delete("/{group_id}/students/{student_id}", status_code=204)
async def delete_student(
    group_id: str,
    student_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    # Verify group exists and belongs to current user
    result = await db.execute(
        select(Group).where(Group.id == group_id, Group.owner_id == user.id)
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    # Verify student exists in this group
    result = await db.execute(
        select(Student).where(Student.id == student_id, Student.group_id == group_id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    await db.delete(student)
    await db.commit()
    return Response(status_code=204)
