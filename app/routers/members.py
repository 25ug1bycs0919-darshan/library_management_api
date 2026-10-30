from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.borrowing import Borrowing
from app.models.member import Member
from app.schemas.member import MemberCreate, MemberRead, MemberUpdate


router = APIRouter(prefix="/members", tags=["Members"])


@router.post("", response_model=MemberRead, status_code=status.HTTP_201_CREATED)
def create_member(
    member_data: MemberCreate,
    db: Session = Depends(get_db),
) -> Member:
    member = Member(**member_data.model_dump())
    db.add(member)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A member with this email already exists.",
        ) from exc
    db.refresh(member)
    return member


@router.get("", response_model=list[MemberRead])
def list_members(db: Session = Depends(get_db)) -> list[Member]:
    return list(db.scalars(select(Member).order_by(Member.id)).all())


@router.get("/{member_id}", response_model=MemberRead)
def get_member(member_id: int, db: Session = Depends(get_db)) -> Member:
    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found.",
        )
    return member


@router.put("/{member_id}", response_model=MemberRead)
def update_member(
    member_id: int,
    member_data: MemberUpdate,
    db: Session = Depends(get_db),
) -> Member:
    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found.",
        )

    for field, value in member_data.model_dump().items():
        setattr(member, field, value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A member with this email already exists.",
        ) from exc
    db.refresh(member)
    return member


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(member_id: int, db: Session = Depends(get_db)) -> Response:
    member = db.get(Member, member_id)
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found.",
        )
    has_history = db.scalar(
        select(Borrowing.id).where(Borrowing.member_id == member_id).limit(1)
    )
    if has_history is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A member with borrowing history cannot be deleted.",
        )
    db.delete(member)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
