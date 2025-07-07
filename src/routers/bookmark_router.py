from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from pydantic import BaseModel
from sqlmodel import Session, select

from authentication import KeycloakUser, get_user_or_raise
from database.session import get_session
from database.model.bookmark.bookmark import Bookmark
from database.model.concept.aiod_entry import AIoDEntryORM  # <-- Import your resource table
from http import HTTPStatus
from database.model.concept.concept import AIoDConcept
from database.model.helper_functions import non_abstract_subclasses


class BookmarkCreate(BaseModel):
    resource_identifier: str


class BookmarkRead(BaseModel):
    resource_identifier: str
    created_at: str


def create(url_prefix: str = "") -> APIRouter:
    router = APIRouter()
    version = "v1"

    for path in [
        f"{url_prefix}/bookmarks/{version}",
        f"{url_prefix}/v2/bookmarks",
        f"{url_prefix}/bookmarks",
    ]:

        @router.get(
            path,
            tags=["Bookmarks"],
            description="Return all assets for which you have bookmarked.",
            response_model=List[BookmarkRead],
        )
        def list_bookmarks(
            user: KeycloakUser = Depends(get_user_or_raise), session: Session = Depends(get_session)
        ) -> List[BookmarkRead]:
            bookmarks = session.exec(
                select(Bookmark).where(Bookmark.user_identifier == user._subject_identifier)
            ).all()
            return [
                BookmarkRead(
                    resource_identifier=bookmark.resource_identifier,
                    created_at=bookmark.created_at.isoformat(),
                )
                for bookmark in bookmarks
            ]

        @router.post(
            path,
            tags=["Bookmarks"],
            response_model=BookmarkRead,
            description="Add a bookmark to an asset for a logged-in user.",
        )
        def create_bookmark(
            bookmark: BookmarkCreate,
            user: KeycloakUser = Depends(get_user_or_raise),
            session: Session = Depends(get_session),
            status_code: HTTPStatus = HTTPStatus.OK,
        ) -> BookmarkRead:
            # # Check if the resource exists
            if not resource_identifier_exists_in_database(bookmark.resource_identifier, session):
                raise HTTPException(
                    status_code=HTTPStatus.NOT_FOUND,
                    detail=f"Resource {bookmark.resource_identifier} does not exist.",
                )

            # Prevent duplicate bookmarks
            existing = session.exec(
                select(Bookmark).where(
                    Bookmark.user_identifier == user._subject_identifier,
                    Bookmark.resource_identifier == bookmark.resource_identifier,
                )
            ).first()
            if existing:
                raise HTTPException(
                    status_code=HTTPStatus.CONFLICT,
                    detail=f"Bookmark already exists for this resource identifier {bookmark.resource_identifier}",
                )

            bookmark = Bookmark(
                user_identifier=user._subject_identifier,
                resource_identifier=bookmark.resource_identifier,
            )
            session.add(bookmark)
            session.commit()
            session.refresh(bookmark)
            return BookmarkRead(
                id=bookmark.id,
                resource_identifier=bookmark.resource_identifier,
                created_at=bookmark.created_at.isoformat(),
            )

        @router.delete(
            path,
            tags=["Bookmarks"],
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
    Returns True if the given platform_resource_identifier exists in any AIoDConcept subclass table.
    """
    asset_types = list(non_abstract_subclasses(AIoDConcept))

    for asset_type in asset_types:
        query = select(asset_type).where(asset_type.identifier == resource_identifier)
        result = session.exec(query).first()

        if result:
            return True

    return False
