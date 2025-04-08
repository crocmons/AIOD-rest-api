from typing import Sequence

from fastapi import APIRouter, Depends

from authentication import KeycloakUser, get_user_or_raise
from database.model.concept.concept import AIoDConcept


def create(url_prefix: str) -> APIRouter:
    router = APIRouter()
    version = "v1"

    router.get(
        f"{url_prefix}/user/resources/{version}",
        tags=["User"],
        description="Return all your assets",
        response_model=None,  # Look at review return stuff
    )(get_resources_for_logged_in_user)
    return router


def get_resources_for_logged_in_user(
    user: KeycloakUser = Depends(get_user_or_raise),
) -> Sequence[AIoDConcept]:
    return _get_resources_for_user(user)


def _get_resources_for_user(user: KeycloakUser) -> Sequence[AIoDConcept]:
    return []
