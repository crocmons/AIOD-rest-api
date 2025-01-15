import enum
from datetime import datetime, timezone
from typing import Literal

import sqlalchemy
from pydantic.main import BaseModel
from sqlalchemy import Column
from sqlmodel import SQLModel, Field


class ReviewStatus(enum.StrEnum):
    ACCEPTED = enum.auto()
    REJECTED = enum.auto()
    PENDING = enum.auto()


class Review(SQLModel, table=True):  # type: ignore [call-arg]
    """A review (which may be pending), requested by a user to publish an asset/change."""

    __tablename__ = "review"

    identifier: int = Field(primary_key=True)
    request_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # We do not want the review to be deleted when the original requestee is deleted,
    # there could be e.g., shared ownership in which case the review data should be preserved.
    requestee_identifier: int | None = Field(
        foreign_key="user.subject_identifier", ondelete="SET NULL"
    )

    # On the other hand, if the entry corresponding to the thing it reviews is removed,
    # then we also want to permanently remove the review data.
    aiod_entry_identifier: int = Field(foreign_key="aiod_entry.identifier", ondelete="CASCADE")

    decision: ReviewStatus = Field(
        sa_column=Column(sqlalchemy.Enum(ReviewStatus)), default=ReviewStatus.PENDING
    )
    reviewer_identifier: int | None = Field(
        foreign_key="user.subject_identifier", ondelete="SET NULL"
    )
    decision_date: datetime | None = Field()

    # Not sure if size should be limited, especially if we want to use this for structured data.
    comment: str = Field()
    change: str = Field()


class Decision(BaseModel):
    review_identifier: int = Field(description="The identifier of the review request.")
    decision: Literal[ReviewStatus.REJECTED, ReviewStatus.ACCEPTED] = Field()
    comment: str = Field()
