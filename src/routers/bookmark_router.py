from fastapi import APIRouter, Depends, HTTPException
from typing import List, Union
from pydantic import BaseModel, validator
from sqlmodel import Session, select, Field

from authentication import KeycloakUser, get_user_or_raise
from database.session import get_session
from database.model.bookmark.bookmark import Bookmark
from http import HTTPStatus
from database.model.concept.concept import AIoDConcept
from database.model.helper_functions import non_abstract_subclasses
from datetime import datetime
from routers.helper_functions import get_asset_type_by_abbreviation


class BookmarkRead(BaseModel):
    resource_identifier: str = Field(description="The identifier of the resource being bookmarked.")
    created_at: datetime = Field(description="The time when the bookmark was created.")

    class Config:
        json_encoders = {datetime: lambda dt: dt.isoformat()}


def create(url_prefix: str = "") -> APIRouter:
    router = APIRouter()

    for path in [
        f"{url_prefix}/v2/bookmarks",
        f"{url_prefix}/bookmarks",
    ]:

        @router.get(
            path,
            tags=["User"],
            description="Return all assets for you have bookmarked.",
            response_model=List[BookmarkRead],
        )
        def list_bookmarks(
            user: KeycloakUser = Depends(get_user_or_raise), session: Session = Depends(get_session)
        ) -> List[BookmarkRead]:
            return session.exec(
                select(Bookmark).where(Bookmark.user_identifier == user._subject_identifier)
            ).all()

        @router.post(
            path,
            tags=["User"],
            response_model=BookmarkRead,
            description="Add the asset to the logged-in user's bookmarks.",
            status_code=HTTPStatus.OK,
        )
        def create_bookmark(
            resource_identifier: str,
            user: KeycloakUser = Depends(get_user_or_raise),
            session: Session = Depends(get_session),
        ) -> BookmarkRead:
            # # Check if the resource exists
            if not resource_identifier_exists_in_database(resource_identifier, session):
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f"Resource {resource_identifier} does not exist.",
                )

            # Prevent duplicate bookmarks
            db_bookmark = session.exec(
                select(Bookmark).where(
                    Bookmark.user_identifier == user._subject_identifier,
                    Bookmark.resource_identifier == resource_identifier,
                )
            ).first()

            if not db_bookmark:
                db_bookmark = Bookmark(
                    user_identifier=user._subject_identifier,
                    resource_identifier=resource_identifier,
                )
                session.add(db_bookmark)
                session.commit()
                session.refresh(db_bookmark)
            return BookmarkRead(
                resource_identifier=db_bookmark.resource_identifier,
                created_at=db_bookmark.created_at,
            )

        @router.delete(
            path,
            tags=["User"],
            description="Delete a bookmark for the logged-in user by resource identifier",
            status_code=HTTPStatus.OK,
        )
        def delete_bookmark(
            resource_identifier: str,
            user: KeycloakUser = Depends(get_user_or_raise),
            session: Session = Depends(get_session),
        ):
            bookmark = session.exec(
                select(Bookmark).where(
                    Bookmark.user_identifier == user._subject_identifier,
                    Bookmark.resource_identifier == resource_identifier,
                )
            ).first()
            if not bookmark:
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f"Bookmark for resource {resource_identifier} not found.",
                )
            session.delete(bookmark)
            session.commit()
            return None

    return router


def resource_identifier_exists_in_database(resource_identifier: str, session: Session) -> bool:
    """
    Returns True if the given identifier exists in any of the tables.
    """
    asset_type = get_asset_type_by_abbreviation().get(resource_identifier.split("_")[0], None)
    if asset_type:
        query = select(asset_type).where(asset_type.identifier == resource_identifier)
        return session.exec(query).first() is not None

    return False
