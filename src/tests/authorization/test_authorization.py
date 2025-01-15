import contextlib
from http import HTTPStatus
from unittest.mock import Mock

import pytest

from authentication import keycloak_openid, KeycloakUser
from database.authorization import (
    User,
    register_user,
    add_administrator,
)
from database.model.concept.aiod_entry import EntryStatus
from database.session import DbSession
from main import EntryStatusChangeRequest

# "default-roles-aiod"
ALICE = (User(subject_identifier="Alice"), {"edit_aiod_resources"})
BOB = (User(subject_identifier="Bob"), {"edit_aiod_resources"})
REVIEWER = (User(subject_identifier="Reviewer"), {"reviewer", "edit_aiod_resources"})


@contextlib.contextmanager
def logged_in_user(user: User, roles: set[str]):
    original = keycloak_openid.introspect
    keycloak_openid.introspect = Mock(
        return_value={
            "realm_access": {"roles": roles},
            "resource_access": {
                "account": {"roles": ["manage-account", "manage-account-links", "view-profile"]}
            },
            "scope": "openid profile email",
            "username": user.subject_identifier,
            "token_type": "Bearer",
            "active": True,
            "sub": f"{user.subject_identifier}-sub",
        }
    )
    yield
    keycloak_openid.introspect = original


def test_user_must_be_logged_in_to_publish(client, publication):
    response = client.post("/publications/v1", content=publication.json(), headers=None)
    assert response.status_code == HTTPStatus.UNAUTHORIZED

    with logged_in_user(*ALICE):
        response = client.post(
            "/publications/v1", content=publication.json(), headers={"Authorization": "Fake token"}
        )
        assert response.status_code == HTTPStatus.OK, response.json()


def test_new_asset_is_draft(client, publication, mocked_privileged_token: Mock):
    with logged_in_user(*ALICE):
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
    with logged_in_user(*ALICE):
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
    with logged_in_user(*ALICE):
        response = client.post(
            "/publications/v1", content=publication.json(), headers={"Authorization": "Fake token"}
        )
        assert response.status_code == HTTPStatus.OK, response.json()
        identifier = response.json()["identifier"]

        submission = client.post(
            f"/publications/submit/v1/{identifier}",
            headers={"Authorization": "Fake token"},
        )
        assert submission.status_code == HTTPStatus.OK, response.json()
        assert submission.json()["aiod_entry"]["status"] == EntryStatus.SUBMITTED


def test_user_can_not_submit_other_for_review(client, publication):
    with logged_in_user(*ALICE):
        response = client.post(
            "/publications/v1", content=publication.json(), headers={"Authorization": "Fake token"}
        )
        assert response.status_code == HTTPStatus.OK, response.json()
        identifier = response.json()["identifier"]

    with logged_in_user(*BOB):
        submission = client.post(
            f"/publications/submit/v1/{identifier}",
            content=EntryStatusChangeRequest(
                concept_identifier=int(identifier),
                requested_status=EntryStatus.SUBMITTED,
                comment=None,
            ).json(),
            headers={"Authorization": "Fake token"},
        )
        assert submission.status_code == HTTPStatus.FORBIDDEN, response.json()


def test_user_can_retract_assets(client, publication):
    with logged_in_user(*ALICE):
        response = client.post(
            "/publications/v1", content=publication.json(), headers={"Authorization": "Fake token"}
        )
        identifier = response.json()["identifier"]
        response = client.post(
            f"/publications/submit/v1/{identifier}", headers={"Authorization": "Fake token"}
        )
        assert response.json()["aiod_entry"]["status"] == EntryStatus.SUBMITTED
        response = client.post(
            f"/publications/retract/v1/{identifier}", headers={"Authorization": "Fake token"}
        )
        assert response.json()["aiod_entry"]["status"] == EntryStatus.DRAFT


def test_other_user_can_not_retract_assets(client, publication):
    with logged_in_user(*ALICE):
        response = client.post(
            "/publications/v1", content=publication.json(), headers={"Authorization": "Fake token"}
        )
        identifier = response.json()["identifier"]
        response = client.post(
            f"/publications/submit/v1/{identifier}", headers={"Authorization": "Fake token"}
        )
        assert response.json()["aiod_entry"]["status"] == EntryStatus.SUBMITTED

    with logged_in_user(*BOB):
        response = client.post(
            f"/publications/retract/v1/{identifier}", headers={"Authorization": "Fake token"}
        )
        assert response.status_code == HTTPStatus.FORBIDDEN, response.json()


@pytest.mark.parametrize("status", EntryStatus)
def test_user_can_always_delete_asset(status: EntryStatus, publication, client):
    alice, roles = ALICE
    kc_alice = KeycloakUser("alice", roles, alice.subject_identifier)
    with DbSession() as session:
        publication.aiod_entry.status = status
        session.add(publication)
        register_user(kc_alice, session)
        add_administrator(kc_alice, publication, session)
        session.commit()
        identifier = publication.identifier

    with logged_in_user(*ALICE):
        response = client.delete(
            f"/publications/v1/{identifier}",
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()


@pytest.mark.skip()
def test_user_can_edit_asset_in_draft():
    assert ..., "Users should be able to edit their asset while in draft."


@pytest.mark.skip()
def test_user_cannot_edit_asset_in_submission():
    assert ..., "Users can not edit assets under submission."
    # This is the avoid race conditions with the reviewer workflow


@pytest.mark.skip()
def test_only_reviewer_can_approve_submission():
    assert ..., "Only reviewers should be able to approve a submission"
    assert ..., "Reviewers should be able to approve submissions"
    assert ..., "An accepted submission should result in 'published' status."


@pytest.mark.skip()
def test_reviewer_cannot_approve_own_submission():
    assert ..., "A user cannot approve their own submission."
