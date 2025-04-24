import pytest
import mock
from io import BytesIO
from werkzeug.exceptions import NotFound


from dmapiclient import SpotlightAPIClient
from dmapiclient import HTTPError


@pytest.fixture
def spotlight_api_client():
    return SpotlightAPIClient(
        spotlight_duns_api_client_kwargs={
            'base_url': 'http://spotlight-baseurl',
            'api_key': 'api-key',
            'enabled': True
        },
        spotlight_warm_up_api_client_kwargs={
            'base_url': 'http://spotlight-baseurl',
            'api_key': 'api-key',
            'enabled': True
        },
        spotlight_fvra_single_check_api_client_kwargs={
            'base_url': 'http://spotlight-baseurl',
            'api_key': 'api-key',
            'enabled': True
        },
        spotlight_fvra_multiple_check_api_client_kwargs={
            'base_url': 'http://spotlight-baseurl',
            'api_key': 'api-key',
            'enabled': True
        }
    )


class TestSpotlightAPIClient(object):
    @pytest.mark.parametrize(
        'spotlight_client',
        (
            '_spotlight_duns_api_client',
            '_spotlight_warm_up_api_client',
            '_spotlight_fvra_single_check_api_client',
            '_spotlight_fvra_multiple_check_api_client',
        )
    )
    def test_base_headers_are_set_for_each_client(self, spotlight_api_client, rmock, spotlight_client):
        rmock.request(
            "GET",
            "http://spotlight-baseurl/",
            json={},
            status_code=200
        )

        api_client = getattr(spotlight_api_client, spotlight_client)

        api_client._request('GET', '/')

        assert rmock.last_request.headers.get("Content-type") == "application/json"
        assert rmock.last_request.headers.get("Authorization") is None
        assert rmock.last_request.headers.get("User-Agent").startswith("DM-API-Client/")

    def test_init_app_sets_attributes(self, spotlight_api_client):
        app = mock.Mock()
        app.config = {
            "DM_SPOTLIGHT_API_URLS": "DM_SPOTLIGHT_DUNS_API_URL=http://example/a,"
                                     "DM_SPOTLIGHT_FVRA_WARM_UP_API_URL=http://example/b,"
                                     "DM_SPOTLIGHT_FVRA_SINGLE_CHECK_API_URL=http://example/c,"
                                     "DM_SPOTLIGHT_FVRA_MULTIPLE_CHECK_API_URL=http://example/d",
            "DM_SPOTLIGHT_API_KEYS": "DM_SPOTLIGHT_DUNS_API_KEY=example-api-key-a,"
                                     "DM_SPOTLIGHT_FVRA_WARM_UP_API_KEY=example-api-key-b,"
                                     "DM_SPOTLIGHT_FVRA_SINGLE_CHECK_API_KEY=example-api-key-c,"
                                     "DM_SPOTLIGHT_FVRA_MULTIPLE_CHECK_API_KEY=example-api-key-d"
        }
        spotlight_api_client.init_app(app)

        assert spotlight_api_client._spotlight_duns_api_client.base_url == "http://example/a"
        assert spotlight_api_client._spotlight_duns_api_client.api_key == "example-api-key-a"

        assert spotlight_api_client._spotlight_warm_up_api_client.base_url == "http://example/b"
        assert spotlight_api_client._spotlight_warm_up_api_client.api_key == "example-api-key-b"

        assert spotlight_api_client._spotlight_fvra_single_check_api_client.base_url == "http://example/c"
        assert spotlight_api_client._spotlight_fvra_single_check_api_client.api_key == "example-api-key-c"

        assert spotlight_api_client._spotlight_fvra_multiple_check_api_client.base_url == "http://example/d"
        assert spotlight_api_client._spotlight_fvra_multiple_check_api_client.api_key == "example-api-key-d"

    @pytest.mark.parametrize(
        'spotlight_client',
        (
            '_spotlight_duns_api_client',
            '_spotlight_warm_up_api_client',
            '_spotlight_fvra_single_check_api_client',
            '_spotlight_fvra_multiple_check_api_client',
        )
    )
    def test_get_status(self, spotlight_api_client, spotlight_client):
        with pytest.raises(NotFound, match="404 Not Found"):
            api_client = getattr(spotlight_api_client, spotlight_client)

            api_client.get_status()


class TestFindOrganisationFromDunsNumber:
    def test_find_organisation_from_duns_number(self, spotlight_api_client, rmock):
        rmock.post(
            "http://spotlight-baseurl/workflows/5319fad3d7e341a89183b32df72671ba/triggers/manual/paths/invoke"
            "?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=api-key",
            json={"searchOrganisation": [{"DunsNumber": "123456789"}]},
            status_code=200
        )
        result = spotlight_api_client.find_organisation_from_duns_number("123456789")

        assert result == {"organisations": {"DunsNumber": "123456789"}}
        assert rmock.called
        assert rmock.last_request.json() == {
            "requestType": "SearchOrganisation",
            "parameters": {
                "dunsNumber": '123456789'
            }
        }

    def test_find_organisation_from_duns_number_not_found(self, spotlight_api_client, rmock):
        rmock.post(
            "http://spotlight-baseurl/workflows/5319fad3d7e341a89183b32df72671ba/triggers/manual/paths/invoke"
            "?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=api-key",
            body=BytesIO(b'The parameters provided are invalid, please use a different combination and try again.'),
            status_code=200
        )
        try:
            spotlight_api_client.find_organisation_from_duns_number("123456789")
        except HTTPError:
            assert rmock.called


class TestInformSpotlightOfDunsNumberForCheck:
    def test_inform_spotlight_of_duns_number_for_check(self, spotlight_api_client, rmock):
        rmock.post(
            "http://spotlight-baseurl/workflows/91fa768cca7348cab37695fcf34b1262/triggers/Trigger/paths/invoke"
            "?api-version=2016-10-01&sp=%2Ftriggers%2FTrigger%2Frun&sv=1.0&sig=api-key",
            body=BytesIO(b"'Call received.'"),
            status_code=200
        )
        result = spotlight_api_client.inform_spotlight_of_duns_number_for_check("123456789", "Vandham")

        assert result == {"message": "done"}
        assert rmock.called
        assert rmock.last_request.json() == {
            "Account": [
                {
                    "Name": "Vandham",
                    "DunsNumber": "123456789",
                    "OnDemandChecks": "true",
                    "PartOfDailyChecks": "false"
                }
            ]
        }

    def test_find_organisation_from_duns_number_not_found(self, spotlight_api_client, rmock):
        rmock.post(
            "http://spotlight-baseurl/workflows/91fa768cca7348cab37695fcf34b1262/triggers/Trigger/paths/invoke"
            "?api-version=2016-10-01&sp=%2Ftriggers%2FTrigger%2Frun&sv=1.0&sig=api-key",
            body=BytesIO(b"'Something else'"),
            status_code=200
        )
        try:
            spotlight_api_client.inform_spotlight_of_duns_number_for_check("123456789", "Vandham")
        except HTTPError:
            assert rmock.called


class TestGetFinancialsFromDunsNumber:
    def test_get_financials_from_duns_number(self, spotlight_api_client, rmock):
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
        result = spotlight_api_client.get_financials_from_duns_number("123456789")

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


class TestGetFinancialsFromDunsNumbers:
    def test_get_financials_from_duns_numbers(self, spotlight_api_client, rmock):
        rmock.post(
            "http://spotlight-baseurl/workflows/6d3d793e151a4a2c86af189bcca435dd/triggers/Trigger/paths/invoke"
            "?api-version=2016-10-01&sp=%2Ftriggers%2FTrigger%2Frun&sv=1.0&sig=api-key",
            json={
                "ResultSets": {
                    "Table1": [
                        {
                            "DUNS": "123456789",
                            "OrganisationName": "NLA Corp",
                        },
                        {
                            "DUNS": "456789123",
                            "OrganisationName": "BLADE Corp",
                        }
                    ]
                }
            },
            status_code=200
        )
        result = spotlight_api_client.get_financials_from_duns_numbers(["123456789", "456789123"])

        assert result == {
            "organisationMetrics": [
                {
                    "DUNS": "123456789",
                    "OrganisationName": "NLA Corp",
                },
                {
                    "DUNS": "456789123",
                    "OrganisationName": "BLADE Corp",
                }
            ]
        }
        assert rmock.called
        assert rmock.last_request.json() == {
            "Account": [
                {
                    "DunsNumber": [
                        "123456789",
                        "456789123"
                    ],
                    "OnDemandChecks": "true",
                    "PartOfDailyChecks": "false"
                }
            ]
        }
