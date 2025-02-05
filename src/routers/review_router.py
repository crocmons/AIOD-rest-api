import enum
from typing import Sequence

from fastapi import APIRouter
from sqlmodel import select

from database.session import DbSession
from database.review import Submission


def create(url_prefix: str) -> APIRouter:
    router = APIRouter()
    version = "v1"

    router.get(
        f"{url_prefix}/submissions/{version}/",
        tags=["Reviewing"],
        description="List all assets submitted for review.",
    )(list_submissions)

    return router


class ListMode(enum.StrEnum):
    OLDEST = enum.auto()
    NEWEST = enum.auto()
    ALL = enum.auto()
    PENDING = enum.auto()
    COMPLETED = enum.auto()


def list_submissions(mode: ListMode = ListMode.NEWEST) -> Sequence[Submission]:
    with DbSession() as session:
        submissions = select(Submission).order_by(Submission.request_date)
        match mode:
            case ListMode.OLDEST:
                return [session.scalars(submissions).first()]
            case ListMode.ALL:
                return session.scalars(submissions).all()
            case ListMode.PENDING:
                raise NotImplementedError()
            case ListMode.COMPLETED:
                raise NotImplementedError()
            case _:
                return [session.scalars(submissions).first()]
