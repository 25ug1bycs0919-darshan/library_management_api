from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.book import Book
from app.models.borrowing import Borrowing
from app.models.member import Member
from app.schemas.borrowing import BorrowingCreate, BorrowingRead


router = APIRouter(prefix="/borrowings", tags=["Borrowings"])
MAX_BOOKS_PER_MEMBER = 5


@router.post("/issue", response_model=BorrowingRead, status_code=status.HTTP_201_CREATED)
def issue_book(
    borrowing_data: BorrowingCreate,
    db: Session = Depends(get_db),
) -> Borrowing:
    book = db.get(Book, borrowing_data.book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found.",
        )

    member = db.get(Member, borrowing_data.member_id)
    if member is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found.",
        )
    if book.available_copies < 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This book is not currently available.",
        )

    active_borrowings = db.scalar(
        select(func.count())
        .select_from(Borrowing)
        .where(
            Borrowing.member_id == member.id,
            Borrowing.returned_at.is_(None),
        )
    )
    if active_borrowings >= MAX_BOOKS_PER_MEMBER:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A member cannot borrow more than five books at a time.",
        )

    borrowing = Borrowing(
        book_id=book.id,
        member_id=member.id,
        borrowed_at=datetime.now(timezone.utc),
    )
    book.available_copies -= 1
    db.add(borrowing)
    db.commit()
    db.refresh(borrowing)
    return borrowing


@router.post("/{borrowing_id}/return", response_model=BorrowingRead)
def return_book(borrowing_id: int, db: Session = Depends(get_db)) -> Borrowing:
    borrowing = db.get(Borrowing, borrowing_id)
    if borrowing is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Borrowing record not found.",
        )
    if borrowing.returned_at is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This book has already been returned.",
        )

    book = db.get(Book, borrowing.book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The book for this borrowing record no longer exists.",
        )
    book.available_copies += 1
    borrowing.returned_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(borrowing)
    return borrowing


@router.get("", response_model=list[BorrowingRead])
def list_borrowed_books(db: Session = Depends(get_db)) -> list[Borrowing]:
    statement = (
        select(Borrowing)
        .where(Borrowing.returned_at.is_(None))
        .order_by(Borrowing.borrowed_at.desc())
    )
    return list(db.scalars(statement).all())


@router.get("/history", response_model=list[BorrowingRead])
def list_borrowing_history(
    member_id: int | None = None,
    db: Session = Depends(get_db),
) -> list[Borrowing]:
    statement = select(Borrowing).order_by(Borrowing.borrowed_at.desc())
    if member_id is not None:
        statement = statement.where(Borrowing.member_id == member_id)
    return list(db.scalars(statement).all())
