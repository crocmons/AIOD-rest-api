pytest_plugins = ["tests.testutils.default_instances", "tests.testutils.default_sqlalchemy"]


def pytest_generate_tests(metafunc):
    # We want to automatically test endpoints on all supported versions,
    # and allow version-specific tests to be written using a
    # @pytest.mark.versions("vX") marker
    if "client" in metafunc.fixturenames:
        version_marker = next((m for m in metafunc.definition.own_markers if m.name == "versions"), None)
        versions = version_marker.args if version_marker else ["", "v2"]
        metafunc.parametrize(
            "client", versions, indirect=True
        )
