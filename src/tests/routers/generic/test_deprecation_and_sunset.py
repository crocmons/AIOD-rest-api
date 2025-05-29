from http import HTTPStatus

import pytest
from starlette.testclient import TestClient


@pytest.mark.versions("v1")
def test_version_1(client: TestClient):
    response = client.get("/datasets/v1")
    assert response.status_code == HTTPStatus.OK
    assert 'Deprecation' in response.headers
    assert 'Sunset' in response.headers
    assert 'Link' in response.headers
