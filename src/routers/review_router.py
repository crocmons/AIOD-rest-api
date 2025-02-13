from fastapi import APIRouter
from sqlmodel import select

from database.session import DbSession
from database.review import Submission


def create(url_prefix: str) -> APIRouter:
    router = APIRouter()
    version = "v1"

    router.get(
        f"{url_prefix}/submissions/{version}",
        tags=["Reviewing"],
        description="List all assets submitted for review.",
    )(list_submissions)

    return router


def list_submissions():
    with DbSession() as session:
        submissions = select(Submission)
        return session.scalars(submissions).first()
