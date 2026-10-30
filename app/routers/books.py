from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.book import Book
from app.models.borrowing import Borrowing
from app.schemas.book import BookCreate, BookRead, BookUpdate


router = APIRouter(prefix="/books", tags=["Books"])


@router.post("", response_model=BookRead, status_code=status.HTTP_201_CREATED)
def create_book(book_data: BookCreate, db: Session = Depends(get_db)) -> Book:
    book = Book(
        **book_data.model_dump(),
        available_copies=book_data.total_copies,
    )
    db.add(book)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A book with this ISBN already exists.",
        ) from exc
    db.refresh(book)
    return book


@router.get("", response_model=list[BookRead])
def list_books(db: Session = Depends(get_db)) -> list[Book]:
    return list(db.scalars(select(Book).order_by(Book.id)).all())


@router.get("/{book_id}", response_model=BookRead)
def get_book(book_id: int, db: Session = Depends(get_db)) -> Book:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found.",
        )
    return book


@router.put("/{book_id}", response_model=BookRead)
def update_book(
    book_id: int,
    book_data: BookUpdate,
    db: Session = Depends(get_db),
) -> Book:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found.",
        )

    active_borrowings = db.scalar(
        select(func.count())
        .select_from(Borrowing)
        .where(Borrowing.book_id == book_id, Borrowing.returned_at.is_(None))
    )
    if book_data.total_copies < active_borrowings:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Total copies cannot be less than the number currently borrowed.",
        )

    for field, value in book_data.model_dump().items():
        setattr(book, field, value)
    book.available_copies = book_data.total_copies - active_borrowings

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A book with this ISBN already exists.",
        ) from exc
    db.refresh(book)
    return book


@router.delete("/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_book(book_id: int, db: Session = Depends(get_db)) -> Response:
    book = db.get(Book, book_id)
    if book is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found.",
        )
    has_history = db.scalar(
        select(Borrowing.id).where(Borrowing.book_id == book_id).limit(1)
    )
    if has_history is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A book with borrowing history cannot be deleted.",
        )
    db.delete(book)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
