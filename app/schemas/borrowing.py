from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BorrowingCreate(BaseModel):
    book_id: int
    member_id: int


class BorrowingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    member_id: int
    borrowed_at: datetime
    returned_at: datetime | None
