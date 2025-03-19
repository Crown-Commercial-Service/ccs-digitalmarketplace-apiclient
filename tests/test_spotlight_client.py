import pytest
import mock
from io import BytesIO
from werkzeug.exceptions import NotFound


from dmapiclient import SpotlightDunsAPIClient, SpotlightFvraAPIClient
from dmapiclient import HTTPError


@pytest.fixture
def spotlight_duns_client():
    return SpotlightDunsAPIClient('http://spotlight-baseurl', 'api-key', True)


@pytest.fixture
def spotlight_fvra_client():
    return SpotlightFvraAPIClient('http://spotlight-baseurl', 'api-key', True)


class TestSpotlightDunsAPIClient(object):
    def test_base_headers_are_set(self, spotlight_duns_client, rmock):
        rmock.request(
            "GET",
            "http://spotlight-baseurl/",
            json={},
            status_code=200)

        spotlight_duns_client._request('GET', '/')

        assert rmock.last_request.headers.get("Content-type") == "application/json"
        assert rmock.last_request.headers.get("Authorization") is None
        assert rmock.last_request.headers.get("User-Agent").startswith("DM-API-Client/")

    def test_init_app_sets_attributes(self, spotlight_duns_client):
        app = mock.Mock()
        app.config = {
            "DM_SPOTLIGHT_DUNS_API_URL": "http://example",
            "DM_SPOTLIGHT_DUNS_API_KEY": "example-api-key",
        }
        spotlight_duns_client.init_app(app)

        assert spotlight_duns_client.base_url == "http://example"
        assert spotlight_duns_client.api_key == "example-api-key"

    def test_get_status(self, spotlight_duns_client):
        with pytest.raises(NotFound, match="404 Not Found"):
            spotlight_duns_client.get_status()


class TestFindOrganisationFromDunsNumber:
    def test_find_organisation_from_duns_number(self, spotlight_duns_client, rmock):
        rmock.post(
            "http://spotlight-baseurl/workflows/5319fad3d7e341a89183b32df72671ba/triggers/manual/paths/invoke"
            "?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=api-key",
            json={"searchOrganisation": [{"DunsNumber": "123456789"}]},
            status_code=200
        )
        result = spotlight_duns_client.find_organisation_from_duns_number("123456789")

        assert result == {"organisations": {"DunsNumber": "123456789"}}
        assert rmock.called
        assert rmock.last_request.json() == {
            "requestType": "SearchOrganisation",
            "parameters": {
                "dunsNumber": '123456789'
            }
        }

    def test_find_organisation_from_duns_number_not_found(self, spotlight_duns_client, rmock):
        rmock.post(
            "http://spotlight-baseurl/workflows/5319fad3d7e341a89183b32df72671ba/triggers/manual/paths/invoke"
            "?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=api-key",
            body=BytesIO(b'The parameters provided are invalid, please use a different combination and try again.'),
            status_code=200
        )
        try:
            spotlight_duns_client.find_organisation_from_duns_number("123456789")
        except HTTPError:
            assert rmock.called


class TestSpotlightFvraAPIClient(object):
    def test_base_headers_are_set(self, spotlight_fvra_client, rmock):
        rmock.request(
            "GET",
            "http://spotlight-baseurl/",
            json={},
            status_code=200)

        spotlight_fvra_client._request('GET', '/')

        assert rmock.last_request.headers.get("Content-type") == "application/json"
        assert rmock.last_request.headers.get("Authorization") is None
        assert rmock.last_request.headers.get("User-Agent").startswith("DM-API-Client/")

    def test_init_app_sets_attributes(self, spotlight_fvra_client):
        app = mock.Mock()
        app.config = {
            "DM_SPOTLIGHT_FVRA_API_URL": "http://example",
            "DM_SPOTLIGHT_FVRA_API_KEY": "example-api-key",
        }
        spotlight_fvra_client.init_app(app)

        assert spotlight_fvra_client.base_url == "http://example"
        assert spotlight_fvra_client.api_key == "example-api-key"

    def test_get_status(self, spotlight_fvra_client):
        with pytest.raises(NotFound, match="404 Not Found"):
            spotlight_fvra_client.get_status()


class TestGetFinancialsFromDunsNumber:
    def test_get_financials_from_duns_number(self, spotlight_fvra_client, rmock):
        rmock.post(
            "http://spotlight-baseurl/workflows/9f848cc1409f441ca6bae23793ba7960/triggers/Trigger/paths/invoke"
            "?api-version=2016-10-01&sp=%2Ftriggers%2FTrigger%2Frun&sv=1.0&sig=api-key",
            json={
                "ResultSets": [
                    {
                        "DUNS": "123456789",
                        "OrganisationName": "NLA Corp",
                    }
                ]
            },
            status_code=200
        )
        result = spotlight_fvra_client.get_financials_from_duns_number("123456789")

        assert result == {
            "organisationMetrics": {
                "DUNS": "123456789",
                "OrganisationName": "NLA Corp",
            }
        }
        assert rmock.called
        assert rmock.last_request.json() == {
            "Account": [
                {
                    "DunsNumber": "123456789",
                    "OnDemandChecks": "true",
                    "PartOfDailyChecks": "false"
                }
            ]
        }

    def test_get_financials_from_duns_number_not_found(self, spotlight_fvra_client, rmock):
        rmock.post(
            "http://spotlight-baseurl/workflows/9f848cc1409f441ca6bae23793ba7960/triggers/Trigger/paths/invoke"
            "?api-version=2016-10-01&sp=%2Ftriggers%2FTrigger%2Frun&sv=1.0&sig=api-key",
            json={
                "ResultSets": [
                    {
                        "DUNS": "123456789",
                        "OrganisationName": "",
                    }
                ]
            },
            status_code=200
        )
        try:
            spotlight_fvra_client.get_financials_from_duns_number("123456789")
        except HTTPError:
            assert rmock.called
