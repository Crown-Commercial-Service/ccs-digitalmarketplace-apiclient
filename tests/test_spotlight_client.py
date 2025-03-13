import pytest
import mock
from io import BytesIO
from werkzeug.exceptions import NotFound


from dmapiclient import SpotlightDunsAPIClient
from dmapiclient import HTTPError


@pytest.fixture
def spotlight_client():
    return SpotlightDunsAPIClient('http://spotlight-baseurl', 'api-key', True)


class TestSpotlightDunsAPIClient(object):
    def test_base_headers_are_set(self, spotlight_client, rmock):
        rmock.request(
            "GET",
            "http://spotlight-baseurl/",
            json={},
            status_code=200)

        spotlight_client._request('GET', '/')

        assert rmock.last_request.headers.get("Content-type") == "application/json"
        assert rmock.last_request.headers.get("Authorization") is None
        assert rmock.last_request.headers.get("User-Agent").startswith("DM-API-Client/")

    def test_init_app_sets_attributes(self, spotlight_client):
        app = mock.Mock()
        app.config = {
            "DM_SPOTLIGHT_DUNS_API_URL": "http://example",
            "DM_SPOTLIGHT_DUNS_API_KEY": "example-api-key",
        }
        spotlight_client.init_app(app)

        assert spotlight_client.base_url == "http://example"
        assert spotlight_client.api_key == "example-api-key"

    def test_get_status(self, spotlight_client):
        with pytest.raises(NotFound, match="404 Not Found"):
            spotlight_client.get_status()


class TestFindOrganisationFromDunsNumber:
    def test_find_organisation_from_duns_number(self, spotlight_client, rmock):
        rmock.post(
            "http://spotlight-baseurl/workflows/5319fad3d7e341a89183b32df72671ba/triggers/manual/paths/invoke"
            "?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=api-key",
            json={"searchOrganisation": [{"DunsNumber": "123456789"}]},
            status_code=200
        )
        result = spotlight_client.find_organisation_from_duns_number("123456789")

        assert result == {"organisations": {"DunsNumber": "123456789"}}
        assert rmock.called
        assert rmock.last_request.json() == {
            "requestType": "SearchOrganisation",
            "parameters": {
                "dunsNumber": '123456789'
            }
        }

    def test_find_organisation_from_duns_number_not_found(self, spotlight_client, rmock):
        rmock.post(
            "http://spotlight-baseurl/workflows/5319fad3d7e341a89183b32df72671ba/triggers/manual/paths/invoke"
            "?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=api-key",
            body=BytesIO(b'The parameters provided are invalid, please use a different combination and try again.'),
            status_code=200
        )
        try:
            spotlight_client.find_organisation_from_duns_number("123456789")
        except HTTPError:
            assert rmock.called
