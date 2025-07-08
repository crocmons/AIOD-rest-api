from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, String


class BookmarkBase(SQLModel):
    user_identifier: str = Field(
        foreign_key="user.subject_identifier", nullable=False, ondelete="CASCADE"
    )
    resource_identifier: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Bookmark(BookmarkBase, table=True):  # type: ignore [call-arg]
    id: Optional[int] = Field(default=None, primary_key=True)
    __tablename__ = "bookmark"
