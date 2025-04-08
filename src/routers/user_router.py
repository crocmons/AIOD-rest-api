from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlmodel import Session

from authentication import KeycloakUser, get_user_or_raise
from database.authorization import Permission, PermissionType
from database.session import get_session
from database.model.concept.aiod_entry import AIoDEntryORM, AIoDEntryRead


def create(url_prefix: str) -> APIRouter:
    router = APIRouter()
    version = "v1"

    router.get(
        f"{url_prefix}/user/resources/{version}",
        tags=["User"],
        description="Return all your assets",
        response_model=list[AIoDEntryRead],  # TODO: Return AIoD Concept instead
    )(get_resources_for_logged_in_user)
    return router


def get_resources_for_logged_in_user(
    user: KeycloakUser = Depends(get_user_or_raise),
    session: Session = Depends(get_session),
) -> list[AIoDEntryORM]:
    return _get_resources_for_user(user, session)


def _get_resources_for_user(user: KeycloakUser, session: Session) -> list[AIoDEntryORM]:
    # Get all resources for which the user has administration permissions
    stmt = (
        select(AIoDEntryORM)
        .join(Permission.aiod_entry)
        .where(
            Permission.user_identifier == user._subject_identifier,
            Permission.type_ == PermissionType.ADMIN,
        )
    )
    entries = session.scalars(stmt).all()
    return entries
