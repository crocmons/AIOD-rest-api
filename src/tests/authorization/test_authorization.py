import contextlib
from http import HTTPStatus
from typing import NamedTuple
from unittest.mock import Mock

import pytest

from authentication import keycloak_openid, KeycloakUser
from database.authorization import (
    register_user,
    add_administrator,
)
from database.model.concept.aiod_entry import EntryStatus
from database.model.concept.concept import AIoDConcept
from database.session import DbSession
from main import EntryStatusChangeRequest


# "default-roles-aiod"
class TestUser(NamedTuple):
    name: str
    roles: set[str]


ALICE = TestUser("Alice", {"edit_aiod_resources"})
BOB = TestUser("Bob", {"edit_aiod_resources"})
REVIEWER = TestUser("Reviewer", {"reviewer", "edit_aiod_resources"})


@contextlib.contextmanager
def logged_in_user(user: TestUser):
    original = keycloak_openid.introspect
    keycloak_openid.introspect = Mock(
        return_value={
            "realm_access": {"roles": user.roles},
            "resource_access": {
                "account": {"roles": ["manage-account", "manage-account-links", "view-profile"]}
            },
            "scope": "openid profile email",
            "username": user.name,
            "token_type": "Bearer",
            "active": True,
            "sub": f"{user.name}-sub",
        }
    )
    yield
    keycloak_openid.introspect = original


def test_user_must_be_logged_in_to_publish(client, publication):
    response = client.post("/publications/v1", content=publication.json(), headers=None)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    with logged_in_user(ALICE):
        response = client.post(
            "/publications/v1", content=publication.json(), headers={"Authorization": "Fake token"}
        )
        assert response.status_code == HTTPStatus.OK, response.json()


def test_new_asset_is_draft(client, publication, mocked_privileged_token: Mock):
    with logged_in_user(ALICE):
        response = client.post(
            "/publications/v1", content=publication.json(), headers={"Authorization": "Fake token"}
        )
        assert response.status_code == HTTPStatus.OK, response.json()

        server_data = client.get(f"/publications/v1/{response.json()['identifier']}").json()
        assert server_data["aiod_entry"]["status"] == EntryStatus.DRAFT


def test_drafts_are_private(
    client,
    publication,
    mocked_privileged_token: Mock,
):
    with logged_in_user(ALICE):
        response = client.post(
            "/publications/v1", content=publication.json(), headers={"Authorization": "Fake token"}
        )
        assert response.status_code == HTTPStatus.OK, response.json()

    response = client.get(f"/publications/v1/{response.json()['identifier']}")
    pytest.skip("Privacy rules not yet implemented.")
    # assert response.status_code == HTTPStatus.FORBIDDEN
    # through list
    # through ES
    # with and without authentication


def test_user_can_submit_draft_for_review(client, publication):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.DRAFT)
    with logged_in_user(ALICE):
        submission = client.post(
            f"/publications/submit/v1/{identifier}",
            headers={"Authorization": "Fake token"},
        )
        assert submission.status_code == HTTPStatus.OK, submission.json()
        assert submission.json()["aiod_entry"]["status"] == EntryStatus.SUBMITTED


def test_user_can_not_submit_other_for_review(client, publication):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.DRAFT)

    with logged_in_user(BOB):
        submission = client.post(
            f"/publications/submit/v1/{identifier}",
            content=EntryStatusChangeRequest(
                concept_identifier=int(identifier),
                requested_status=EntryStatus.SUBMITTED,
                comment=None,
            ).json(),
            headers={"Authorization": "Fake token"},
        )
        assert submission.status_code == HTTPStatus.FORBIDDEN, submission.json()


def test_user_can_retract_assets(client, publication):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)
    with logged_in_user(ALICE):
        response = client.post(
            f"/publications/retract/v1/{identifier}", headers={"Authorization": "Fake token"}
        )
        assert response.json()["aiod_entry"]["status"] == EntryStatus.DRAFT


def test_other_user_can_not_retract_assets(client, publication):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)

    with logged_in_user(BOB):
        response = client.post(
            f"/publications/retract/v1/{identifier}", headers={"Authorization": "Fake token"}
        )
        assert response.status_code == HTTPStatus.FORBIDDEN, response.json()


@pytest.mark.parametrize("status", EntryStatus)
def test_user_can_always_delete_asset(status: EntryStatus, publication, client):
    identifier = register_asset(publication, owner=ALICE, status=status)

    with logged_in_user(ALICE):
        response = client.delete(
            f"/publications/v1/{identifier}",
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()


def register_asset(asset: AIoDConcept, /, *, owner: TestUser, status: EntryStatus):
    kc_alice = KeycloakUser(owner.name, owner.roles, f"{owner.name}-sub")
    with DbSession() as session:
        asset.aiod_entry.status = status
        session.add(asset)
        register_user(kc_alice, session)
        add_administrator(kc_alice, asset, session)
        session.commit()
        return asset.identifier


def test_user_can_edit_asset_in_draft(publication, client):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.DRAFT)
    new_name = "Alice in Wonderland"

    with logged_in_user(ALICE):
        response = client.put(
            f"/publications/v1/{identifier}",
            content=f'{{"name": "{new_name}"}}',
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()
        updated_publication = client.get(f"/publications/v1/{identifier}").json()
        assert updated_publication["name"] == new_name


def test_user_cannot_edit_asset_in_submission(publication, client):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)
    new_name = "Alice in Wonderland"

    with logged_in_user(ALICE):
        response = client.put(
            f"/publications/v1/{identifier}",
            content=f'{{"name": "{new_name}"}}',
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.FORBIDDEN, response.json()


@pytest.mark.skip()
def test_only_reviewer_can_approve_submission():
    assert ..., "Only reviewers should be able to approve a submission"
    assert ..., "Reviewers should be able to approve submissions"
    assert ..., "An accepted submission should result in 'published' status."


@pytest.mark.skip()
def test_reviewer_cannot_approve_own_submission():
    assert ..., "A user cannot approve their own submission."
