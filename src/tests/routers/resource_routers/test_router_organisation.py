import copy
from unittest.mock import Mock

from starlette import status
from starlette.testclient import TestClient

from database.model.agent.contact import Contact
from database.model.agent.organisation import Organisation
from database.session import DbSession

import pytest


def test_happy_path(
    client: TestClient,
    mocked_privileged_token: Mock,
    organisation: Organisation,
    contact: Contact,
    body_agent: dict,
):
    with DbSession() as session:
        session.add(organisation)  # The new organisation will be a member of this organisation
        session.add(contact)
        session.commit()

    body = copy.copy(body_agent)
    body["platform_resource_identifier"] = "2"
    body["date_founded"] = "2023-01-01"
    body["legal_name"] = "A name for the organisation"
    body["ai_relevance"] = "Part of CLAIRE"
    body["type"] = "Research Institute"
    body["member"] = [1]
    body["contact_details"] = 1
    body["turnover"] = "<1m €"

    response = client.post("/organisations/v1", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()

    response = client.get("/organisations/v1/2")
    assert response.status_code == 200, response.json()

    response_json = response.json()
    assert response_json["identifier"] == 2
    assert response_json["ai_resource_identifier"] == 2
    assert response_json["agent_identifier"] == 2

    assert response_json["date_founded"] == "2023-01-01"
    assert response_json["legal_name"] == "A name for the organisation"
    assert response_json["ai_relevance"] == "Part of CLAIRE"
    assert response_json["type"] == "research institute"
    assert response_json["member"] == [1]
    assert response_json["contact_details"] == 1
    assert response_json["turnover"] == "<1m €"

    # response = client.delete("/organisations/v1/1", headers={"Authorization": "Fake token"})
    # assert response.status_code == 200
    # response = client.get("/organisations/v1/2")
    # assert response.status_code == 200, response.json()
    # response_json = response.json()
    # TODO(jos): make sure Agent is deleted on CASCADE

    body["type"] = "Association"
    response = client.put("organisations/v1/2", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    response = client.get("organisations/v1/2")
    assert response.json()["type"] == "association"

    body["number_of_employees"] = "<50"
    response = client.put("organisations/v1/2", json=body, headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()
    response = client.get("organisations/v1/2")
    assert response.json()["number_of_employees"] == "<50"

    response = client.delete("/organisations/v1/2", headers={"Authorization": "Fake token"})
    assert response.status_code == 200, response.json()


@pytest.mark.parametrize("field, invalid_value, expected_values", [
    ("turnover", "100m €", ["<1m €", ">1m €", ">3m €", ">5m €", ">50m €", ">1.5b €"]),
    ("number_of_employees", "1000", ["<10", "<50", "<250", ">250"]),

])
def test_invalid_literal_values_for_turnover_and_employees(
    client: TestClient,
    mocked_privileged_token: Mock,
    organisation: Organisation,
    contact: Contact,
    body_agent: dict,
    field: str,
    invalid_value: str,
    expected_values: list,
):
    with DbSession() as session:
        session.add(organisation)  # The new organisation will be a member of this organisation
        session.add(contact)
        session.commit()

    body = copy.copy(body_agent)
    body["platform_resource_identifier"] = "2"
    body["date_founded"] = "2023-01-01"
    body["legal_name"] = "Test Org"
    body["ai_relevance"] = "AI focused"
    body["type"] = "Research Institute"
    body["member"] = [1]
    body["contact_details"] = 1
    body[field] = invalid_value

    response = client.post("/organisations/v1", json=body, headers={"Authorization": "Fake token"})

    for value in expected_values:
        assert value in response.json()["detail"][0]["msg"]
