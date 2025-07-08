from http import HTTPStatus

from starlette.testclient import TestClient
from database.session import DbSession

from tests.testutils.users import logged_in_user, ALICE
from database.model.bookmark.bookmark import Bookmark
from database.session import DbSession
from tests.testutils.users import register_asset
from datetime import datetime
from database.model.agent.person import Person
from database.model.agent.contact import Contact
from database.authorization import User

def test_create_bookmark(
    client: TestClient,
    person: Person) -> None:

    register_asset(person)
    response = client.get("/persons")
    identifier = response.json()[0]["identifier"]

    with logged_in_user():
        response = client.post(
            "/bookmarks",
            json={"resource_identifier": identifier},
            headers={"Authorization": "fake token"},
        )
    assert response.status_code == HTTPStatus.OK
    bookmark = response.json()
    assert bookmark["resource_identifier"] == identifier
    assert bookmark["created_at"] is not None

    # Create bookmark for non existing resource.
    with logged_in_user():
        response = client.post(
            "/bookmarks",
            json={"resource_identifier": "wrong_indetifier"},
            headers={"Authorization": "fake token"},
        )

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json()["detail"] == f"Resource wrong_indetifier does not exist."



def test_create_duplicate(
    client: TestClient,
    person: Person
) -> None:

    identifier = register_asset(person)
    with DbSession() as session:
        session.add(User(subject_identifier=ALICE._subject_identifier))
        session.commit()

        bookmark = Bookmark(
            user_identifier=ALICE._subject_identifier,
            resource_identifier=identifier,
            created_at=datetime.now()
        )
        session.add(bookmark)
        session.commit()

    # Attempt to create a duplicate bookmark
    with logged_in_user(ALICE):
        response = client.post(
            "/bookmarks",
            json={"resource_identifier": identifier},
            headers={"Authorization": "fake token"},
        )

    assert response.status_code == HTTPStatus.CONFLICT
    assert response.json()["detail"] == (
        f"Bookmark already exists for this resource identifier {identifier}"
    )


def test_get_bookmarks(client: TestClient, person: Person, contact: Contact) -> None:

    prsn_id = register_asset(person)
    contact_id = register_asset(contact)

    with DbSession() as session:
        session.add(User(subject_identifier=ALICE._subject_identifier))
        session.commit()

    # Add a bookmark
    with logged_in_user(ALICE):
        response = client.post(
            "/bookmarks",
            json={"resource_identifier": prsn_id},
            headers={"Authorization": "fake token"},
        )
        assert response.status_code == HTTPStatus.OK

        response = client.post(
            "/bookmarks",
            json={"resource_identifier": contact_id},
            headers={"Authorization": "fake token"},
        )
        assert response.status_code == HTTPStatus.OK

        # Fetch bookmarks
        response = client.get(
            "/bookmarks",
            headers={"Authorization": "fake token"},
        )

        assert response.status_code == HTTPStatus.OK
        bookmarks = response.json()
        assert len(bookmarks) == 2

def test_delete_bookmark(
    client: TestClient,
    person: Person
) -> None:
    identifier = register_asset(person)

    with DbSession() as session:
        session.add(User(subject_identifier=ALICE._subject_identifier))
        session.commit()

    with logged_in_user(ALICE):
        response = client.post(
            "/bookmarks",
            json={"resource_identifier": identifier},
            headers={"Authorization": "fake token"},
        )
    assert response.status_code == HTTPStatus.OK


    with logged_in_user(ALICE):
        response = client.delete(
            f"/bookmarks?resource_identifier={identifier}",
            headers={"Authorization": "fake token"},
            )
    assert response.status_code == HTTPStatus.OK
    assert response.json() == None

    # Confirm it's deleted
    with logged_in_user(ALICE):
        response = client.get(
            "/bookmarks",
            headers={"Authorization": "fake token"},
        )
    assert response.status_code == HTTPStatus.OK
    assert all(b["resource_identifier"] != identifier for b in response.json())
