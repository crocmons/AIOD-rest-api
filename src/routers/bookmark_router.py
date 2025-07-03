from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from pydantic import BaseModel
from sqlmodel import Session, select

from authentication import KeycloakUser, get_user_or_raise
from database.session import get_session
from database.model.bookmark.bookmark import Bookmark
from database.model.concept.aiod_entry import AIoDEntryORM  # <-- Import your resource table

class BookmarkCreate(BaseModel):
    resource_identifier: str

class BookmarkRead(BaseModel):
    id: int
    resource_identifier: str
    created_at: str

def create(url_prefix: str = "") -> APIRouter:
    router = APIRouter()
    version = "v1"
    
    for path in [
        f"{url_prefix}/user/bookmarks/{version}",
        f"{url_prefix}/v2/user/bookmarks",
        f"{url_prefix}/user/bookmarks",
    ]:
        @router.get(
            f"{url_prefix}/user/bookmarks",
            response_model=List[BookmarkRead],
            tags=["User"],
            summary="List all bookmarks for the current user"
        )
        def list_bookmarks(
            user: KeycloakUser = Depends(get_user_or_raise),
            session: Session = Depends(get_session)
        ) -> List[BookmarkRead]:
            bookmarks = session.exec(
                select(Bookmark).where(Bookmark.user_identifier == user._subject_identifier)
            ).all()
            return [
                BookmarkRead(
                    id=b.id,
                    resource_identifier=b.resource_identifier,
                    created_at=b.created_at.isoformat()
                ) for b in bookmarks
            ]

    @router.post(
        f"{url_prefix}/user/bookmarks",
        response_model=BookmarkRead,
        status_code=status.HTTP_201_CREATED,
        tags=["User"],
        summary="Create a new bookmark for the current user"
    )
    def create_bookmark(
        bookmark_in: BookmarkCreate,
        user: KeycloakUser = Depends(get_user_or_raise),
        session: Session = Depends(get_session)
    ) -> BookmarkRead:
        # Check if the resource exists!
        resource = session.exec(
            select(AIoDEntryORM).where(AIoDEntryORM.identifier == bookmark_in.resource_identifier)
        ).first()
        if not resource:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Resource does not exist"
            )

        # Prevent duplicate bookmarks
        existing = session.exec(
            select(Bookmark).where(
                Bookmark.user_identifier == user._subject_identifier,
                Bookmark.resource_identifier == bookmark_in.resource_identifier
            )
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bookmark already exists for this resource"
            )
        bookmark = Bookmark(
            user_identifier=user._subject_identifier,
            resource_identifier=bookmark_in.resource_identifier
        )
        session.add(bookmark)
        session.commit()
        session.refresh(bookmark)
        return BookmarkRead(
            id=bookmark.id,
            resource_identifier=bookmark.resource_identifier,
            created_at=bookmark.created_at.isoformat()
        )

    @router.delete(
        f"{url_prefix}/user/bookmarks/{{resource_identifier}}",
        status_code=status.HTTP_204_NO_CONTENT,
        tags=["User"],
        summary="Delete a bookmark for the current user by resource identifier"
    )
    def delete_bookmark(
        resource_identifier: str,
        user: KeycloakUser = Depends(get_user_or_raise),
        session: Session = Depends(get_session)
    ):
        bookmark = session.exec(
            select(Bookmark).where(
                Bookmark.user_identifier == user._subject_identifier,
                Bookmark.resource_identifier == resource_identifier
            )
        ).first()
        if not bookmark:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bookmark not found"
            )
        session.delete(bookmark)
        session.commit()
        return None

    return router