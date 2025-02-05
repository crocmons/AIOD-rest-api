import contextlib
from http import HTTPStatus
from unittest.mock import Mock

import pytest

from authentication import keycloak_openid, KeycloakUser
from database.authorization import (
    register_user,
    add_administrator,
)
from database.model.concept.aiod_entry import EntryStatus
from database.model.concept.concept import AIoDConcept
from database.review import Review, Decision, ReviewCreate, Submission
from database.session import DbSession


ALICE = KeycloakUser("Alice", {"edit_aiod_resources"}, "alice-sub")
BOB = KeycloakUser("Bob", {"edit_aiod_resources"}, "bob-sub")
REVIEWER = KeycloakUser("Reviewer", {"reviewer", "edit_aiod_resources"}, "reviewer-sub")


def _register_user_in_db(user: KeycloakUser) -> KeycloakUser:
    with DbSession() as session:
        register_user(user, session)
        session.commit()
    return user


@contextlib.contextmanager
def logged_in_user(user: KeycloakUser):
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
            "sub": user._subject_identifier,
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
        assert "submission_identifier" in submission.json()

    with logged_in_user(REVIEWER):
        queue = client.get("/submissions/v1", headers={"Authorization": "Fake token"})
        assert queue.status_code == HTTPStatus.OK, queue.json()
        assert len(queue.json()) == 1, queue.json()


def test_user_can_not_submit_other_for_review(client, publication):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.DRAFT)

    with logged_in_user(BOB):
        submission = client.post(
            f"/publications/submit/v1/{identifier}",
            headers={"Authorization": "Fake token"},
        )
        assert submission.status_code == HTTPStatus.FORBIDDEN, submission.json()


def test_user_can_retract_assets(client, publication):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)
    with logged_in_user(ALICE):
        response = client.post(
            f"/publications/retract/v1/{identifier}", headers={"Authorization": "Fake token"}
        )
        assert "review_identifier" in response.json()
        assert Decision.RETRACTED == response.json()["decision"]


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


def register_asset(asset: AIoDConcept, /, *, owner: KeycloakUser, status: EntryStatus):
    with DbSession() as session:
        session.add(asset)
        session.commit()

        register_user(owner, session)
        add_administrator(owner, asset, session)

        asset.aiod_entry.status = status
        if status in [EntryStatus.SUBMITTED, EntryStatus.PUBLISHED, EntryStatus.REJECTED]:
            submission = Submission(
                requestee_identifier=owner._subject_identifier,
                aiod_entry_identifier=asset.aiod_entry.identifier,
            )
            session.add(submission)
            if status == EntryStatus.PUBLISHED:
                register_user(REVIEWER, session)
                review = Review(
                    decision=Decision.ACCEPTED,
                    reviewer_identifier=REVIEWER._subject_identifier,
                )
                review.submission = submission
                session.add(review)
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


def test_only_reviewer_can_approve_submission(publication, client):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)
    _register_user_in_db(REVIEWER)

    with logged_in_user(ALICE):
        response = client.post(
            "/publications/review/v1",
            content=str(
                ReviewCreate(decision=Decision.ACCEPTED, submission_identifier=1, comment="").json()
            ),
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.FORBIDDEN, response.json()

    with logged_in_user(REVIEWER):
        response = client.post(
            "/publications/review/v1",
            content=str(
                ReviewCreate(decision=Decision.ACCEPTED, submission_identifier=1, comment="").json()
            ),
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()

    response = client.get(f"/publications/v1/{identifier}")
    assert response.status_code == HTTPStatus.OK, response.json()
    assert response.json()["aiod_entry"]["status"] == EntryStatus.PUBLISHED


def test_reviewer_can_reject_submission(publication, client):
    identifier = register_asset(publication, owner=ALICE, status=EntryStatus.SUBMITTED)
    _register_user_in_db(REVIEWER)

    with logged_in_user(REVIEWER):
        response = client.post(
            "/publications/review/v1",
            content=str(
                ReviewCreate(decision=Decision.REJECTED, submission_identifier=1, comment="").json()
            ),
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.OK, response.json()

    response = client.get(f"/publications/v1/{identifier}")
    assert response.status_code == HTTPStatus.OK, response.json()
    assert response.json()["aiod_entry"]["status"] == EntryStatus.DRAFT


def test_reviewer_cannot_approve_own_submission(publication, client):
    register_asset(publication, owner=REVIEWER, status=EntryStatus.SUBMITTED)
    _register_user_in_db(REVIEWER)

    with logged_in_user(REVIEWER):
        response = client.post(
            "/publications/review/v1",
            content=str(
                ReviewCreate(decision=Decision.ACCEPTED, submission_identifier=1, comment="").json()
            ),
            headers={"Authorization": "Fake token"},
        )
        assert response.status_code == HTTPStatus.FORBIDDEN, response.json()
