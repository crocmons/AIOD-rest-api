import copy
from http import HTTPStatus
from unittest.mock import Mock

import pytest
from starlette.testclient import TestClient

from database.model.concept.aiod_entry import EntryStatus


@pytest.fixture()
def publication_body(body_asset: dict) -> dict:
    body = copy.deepcopy(body_asset)
    body["permanent_identifier"] = "http://dx.doi.org/10.1093/ajae/aaq063"
    body["isbn"] = "9783161484100"
    body["issn"] = "20493630"
    body["type"] = "journal"
    body["content"] = {"plain": "plain content"}
    return body


def test_entry_status_can_update_on_put(
    client: TestClient,
    mocked_privileged_token: Mock,
    publication_body: dict,
):
    response = client.post(
        "/publications/v1", json=publication_body, headers={"Authorization": "Fake token"}
    )
    assert response.status_code == 200, response.json()

    # Default is DRAFT
    response = client.get("/publications/v1/1")
    assert response.status_code == 200, response.json()
    assert response.json()["aiod_entry"]["status"] == EntryStatus.DRAFT
    identifier = response.json()["identifier"]

    publication_body["aiod_entry"]["status"] = EntryStatus.PUBLISHED
    response = client.put(
        f"/publications/v1/{identifier}",
        json=publication_body,
        headers={"Authorization": "Fake token"},
    )
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY, response.json()

    # Status is not updated to published
    response = client.get(f"/publications/v1/{identifier}")
    assert response.status_code == 200, response.json()
    assert response.json()["aiod_entry"]["status"] == EntryStatus.DRAFT
