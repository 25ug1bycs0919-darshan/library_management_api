from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from fastapi import FastAPI

from app.database import Base, engine
from app.models import Book, Borrowing, Member
from app.routers import books, borrowings, members


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Library Management API",
    description="A simple API for books, members, and borrowing records.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(books.router, prefix="/api")
app.include_router(members.router, prefix="/api")
app.include_router(borrowings.router, prefix="/api")
