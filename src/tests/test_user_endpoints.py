from http import HTTPStatus
from typing import Callable

import pytest
from starlette.testclient import TestClient

from database.authorization import set_permission, PermissionType, register_user
from database.model.knowledge_asset.publication import Publication
from database.model.concept.aiod_entry import EntryStatus
from database.model.dataset.dataset import Dataset
from database.session import DbSession
from tests.testutils.users import register_asset, logged_in_user, ALICE, BOB
from tests.testutils.default_instances import publication_factory, publication


def test_my_resources_can_be_empty(client: TestClient) -> None:
    with logged_in_user(ALICE):
        response = client.get("/user/resources/v1", headers={"Authorization": "fake token"})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == [], "A user with no resources should get an empty list"


def test_my_resources_shows_draft_assets(client: TestClient, publication: Publication) -> None:
    register_asset(publication, owner=ALICE, status=EntryStatus.DRAFT)
    with logged_in_user(ALICE):
        response = client.get("/user/resources/v1", headers={"Authorization": "fake token"})
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()) == 1, "Draft assets should be included in this view."


def test_my_resources_shows_published_assets(client: TestClient, publication: Publication) -> None:
    register_asset(publication, owner=ALICE, status=EntryStatus.PUBLISHED)
    with logged_in_user(ALICE):
        response = client.get("/user/resources/v1", headers={"Authorization": "fake token"})
    assert response.status_code == HTTPStatus.OK
    assert len(response.json()) == 1, "Published assets should be included in this view."


@pytest.mark.skip()
def test_my_resources_shows_mixed_assets(client: TestClient, publication: Publication, dataset: Dataset) -> None:
    register_asset(publication, owner=ALICE, status=EntryStatus.DRAFT)
    register_asset(dataset, owner=ALICE, status=EntryStatus.PUBLISHED)
    with logged_in_user(ALICE):
        response = client.get("/user/resources/v1", headers={"Authorization": "fake token"})
    assert response.status_code == HTTPStatus.OK
    assert response.json() == [], ""
    assert True, "The overview should contain attributes specific to each asset"


def test_my_resources_shows_only_own_resources(client: TestClient, publication_factory: Callable[[], Publication]) -> None:
    register_asset(publication_factory(), owner=ALICE, status=EntryStatus.DRAFT)
    register_asset(publication_factory(), owner=ALICE, status=EntryStatus.PUBLISHED)
    register_asset(publication_factory(), owner=BOB, status=EntryStatus.PUBLISHED)

    with logged_in_user(ALICE):
        response = client.get("/user/resources/v1", headers={"Authorization": "fake token"})
        assert len(response.json()) == 2

    with logged_in_user(BOB):
        response = client.get("/user/resources/v1", headers={"Authorization": "fake token"})
        assert len(response.json()) == 1


def test_my_resources_counts_only_if_admin(client: TestClient, publication_factory: Callable[[], Publication]) -> None:
    asset_one = publication_factory()
    identifier_one = register_asset(asset_one, owner=ALICE, status=EntryStatus.PUBLISHED)
    asset_two = publication_factory()
    identifier_two = register_asset(asset_two, owner=ALICE, status=EntryStatus.PUBLISHED)

    with DbSession() as session:
        register_user(BOB, session)
        set_permission(BOB, session.get(Publication, identifier_one).aiod_entry, session, type_=PermissionType.READ)
        set_permission(BOB, session.get(Publication, identifier_two).aiod_entry, session, type_=PermissionType.WRITE)
        session.commit()

    with logged_in_user(BOB):
        response = client.get("/user/resources/v1", headers={"Authorization": "fake token"})
        assert response.json() == []


def test_my_resources_must_be_authorized(client: TestClient) -> None:
    response = client.get("/user/resources/v1")
    assert response.status_code == HTTPStatus.UNAUTHORIZED
