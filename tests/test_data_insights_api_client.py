import pytest
from unittest import mock
from io import BytesIO
from urllib.parse import parse_qs
from werkzeug.exceptions import NotFound


from dmapiclient import DataInsightsAPIClient
from dmapiclient import HTTPError

CERTIFICATE_NUMBER = '7b2a5c3e-1d4f-4a6b-9c8d-0e1f2a3b4c5d'
CERTIFICATE_URL = (
    'http://data-insights-baseurl/workflows/d92a8b97421e4552845c9e6dc0aca5e2/triggers/manual/paths/invoke'
    '/%5Batt%5D.%5BIASMECyberSecurityCertification%5D/?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun'
    f'&sv=1.0&sig=api-key&Filter=CertificateNumber+eq+%27{CERTIFICATE_NUMBER}%27'
)
TOKEN_URL = 'http://login-baseurl/tenant-id/oauth2/v2.0/token'
APIM_CERTIFICATE_URL = (
    'http://apim-baseurl/website-data/manual/paths/invoke/%5Batt%5D.%5BIASMECyberSecurityCertification%5D/'
    f'?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&Filter=CertificateNumber+eq+%27{CERTIFICATE_NUMBER}%27'
)
NO_MATCH_RESPONSE_TEXT = (
    '"The parameter set you have provided is invalid, please provide a valid parameter set in order to return results."'
)


@pytest.fixture
def iasme_apim_api_client():
    return DataInsightsAPIClient(
        iasme_cyber_essentials_api_client_kwargs={
            'base_url': 'http://apim-baseurl',
            'api_key': '',
            'token_url': TOKEN_URL,
            'client_id': 'client-id',
            'client_secret': 'client-secret',
            'scope': 'api://apim/.default',
        },
    )


@pytest.fixture
def data_insights_api_client():
    return DataInsightsAPIClient(
        spotlight_duns_api_client_kwargs={
            'base_url': 'http://data-insights-baseurl',
            'api_key': 'api-key',
            'enabled': True,
        },
        spotlight_warm_up_api_client_kwargs={
            'base_url': 'http://data-insights-baseurl',
            'api_key': 'api-key',
            'enabled': True,
        },
        spotlight_fvra_single_check_api_client_kwargs={
            'base_url': 'http://data-insights-baseurl',
            'api_key': 'api-key',
            'enabled': True,
        },
        spotlight_fvra_multiple_check_api_client_kwargs={
            'base_url': 'http://data-insights-baseurl',
            'api_key': 'api-key',
            'enabled': True,
        },
        iasme_cyber_essentials_api_client_kwargs={
            'base_url': 'http://data-insights-baseurl',
            'api_key': 'api-key',
            'enabled': True,
        },
    )


class TestDataInsightsAPIClient(object):
    @pytest.mark.parametrize(
        'data_insights_client',
        (
            '_spotlight_duns_api_client',
            '_spotlight_warm_up_api_client',
            '_spotlight_fvra_single_check_api_client',
            '_spotlight_fvra_multiple_check_api_client',
            '_iasme_cyber_essentials_api_client',
        ),
    )
    def test_base_headers_are_set_for_each_client(self, data_insights_api_client, rmock, data_insights_client):
        rmock.request('GET', 'http://data-insights-baseurl/', json={}, status_code=200)

        api_client = getattr(data_insights_api_client, data_insights_client)

        api_client._request('GET', '/')

        assert rmock.last_request.headers.get('Content-type') == 'application/json'
        assert rmock.last_request.headers.get('Authorization') is None
        assert rmock.last_request.headers.get('User-Agent').startswith('DM-API-Client/')

    def test_init_app_sets_attributes(self, data_insights_api_client):
        app = mock.Mock()
        app.config = {
            'DM_DATA_INSIGHTS_API_URLS': 'DM_SPOTLIGHT_DUNS_API_URL=http://example/a,'
            'DM_SPOTLIGHT_FVRA_WARM_UP_API_URL=http://example/b,'
            'DM_SPOTLIGHT_FVRA_SINGLE_CHECK_API_URL=http://example/c,'
            'DM_SPOTLIGHT_FVRA_MULTIPLE_CHECK_API_URL=http://example/d,'
            'DM_IASME_CYBER_ESSENTIALS_API_URL=http://example/e',
            'DM_DATA_INSIGHTS_API_KEYS': 'DM_SPOTLIGHT_DUNS_API_KEY=example-api-key-a,'
            'DM_SPOTLIGHT_FVRA_WARM_UP_API_KEY=example-api-key-b,'
            'DM_SPOTLIGHT_FVRA_SINGLE_CHECK_API_KEY=example-api-key-c,'
            'DM_SPOTLIGHT_FVRA_MULTIPLE_CHECK_API_KEY=example-api-key-d,'
            'DM_IASME_CYBER_ESSENTIALS_API_KEY=example-api-key-e',
        }
        data_insights_api_client.init_app(app)

        assert data_insights_api_client._spotlight_duns_api_client.base_url == 'http://example/a'
        assert data_insights_api_client._spotlight_duns_api_client.api_key == 'example-api-key-a'

        assert data_insights_api_client._spotlight_warm_up_api_client.base_url == 'http://example/b'
        assert data_insights_api_client._spotlight_warm_up_api_client.api_key == 'example-api-key-b'

        assert data_insights_api_client._spotlight_fvra_single_check_api_client.base_url == 'http://example/c'
        assert data_insights_api_client._spotlight_fvra_single_check_api_client.api_key == 'example-api-key-c'

        assert data_insights_api_client._spotlight_fvra_multiple_check_api_client.base_url == 'http://example/d'
        assert data_insights_api_client._spotlight_fvra_multiple_check_api_client.api_key == 'example-api-key-d'

        assert data_insights_api_client._iasme_cyber_essentials_api_client.base_url == 'http://example/e'
        assert data_insights_api_client._iasme_cyber_essentials_api_client.api_key == 'example-api-key-e'
        assert data_insights_api_client._iasme_cyber_essentials_api_client.uses_access_token is False

    def test_init_app_sets_iasme_access_token_settings(self, data_insights_api_client, rmock):
        app = mock.Mock()
        app.config = {
            'DM_DATA_INSIGHTS_API_URLS': 'DM_SPOTLIGHT_DUNS_API_URL=http://example/a,'
            'DM_SPOTLIGHT_FVRA_WARM_UP_API_URL=http://example/b,'
            'DM_SPOTLIGHT_FVRA_SINGLE_CHECK_API_URL=http://example/c,'
            'DM_SPOTLIGHT_FVRA_MULTIPLE_CHECK_API_URL=http://example/d,'
            'DM_IASME_CYBER_ESSENTIALS_API_URL=http://apim-baseurl,'
            f'DM_IASME_CYBER_ESSENTIALS_TOKEN_URL={TOKEN_URL},'
            'DM_IASME_CYBER_ESSENTIALS_TOKEN_SCOPE=api://apim/.default',
            'DM_DATA_INSIGHTS_API_KEYS': 'DM_SPOTLIGHT_DUNS_API_KEY=example-api-key-a,'
            'DM_SPOTLIGHT_FVRA_WARM_UP_API_KEY=example-api-key-b,'
            'DM_SPOTLIGHT_FVRA_SINGLE_CHECK_API_KEY=example-api-key-c,'
            'DM_SPOTLIGHT_FVRA_MULTIPLE_CHECK_API_KEY=example-api-key-d,'
            'DM_IASME_CYBER_ESSENTIALS_API_KEY=,'
            'DM_IASME_CYBER_ESSENTIALS_CLIENT_ID=client-id,'
            'DM_IASME_CYBER_ESSENTIALS_CLIENT_SECRET=client-secret',
        }
        data_insights_api_client.init_app(app)
        rmock.post(TOKEN_URL, json={'access_token': 'access-token', 'expires_in': 3599}, status_code=200)
        rmock.get(APIM_CERTIFICATE_URL, json=[{'CertificateLevel': 'CE'}], status_code=200)

        data_insights_api_client.get_cyber_essentials_certificate(CERTIFICATE_NUMBER)

        assert parse_qs(rmock.request_history[0].text) == {
            'grant_type': ['client_credentials'],
            'client_id': ['client-id'],
            'client_secret': ['client-secret'],
            'scope': ['api://apim/.default'],
        }
        assert rmock.last_request.headers['Authorization'] == 'Bearer access-token'

    @pytest.mark.parametrize(
        'spotlight_client',
        (
            '_spotlight_duns_api_client',
            '_spotlight_warm_up_api_client',
            '_spotlight_fvra_single_check_api_client',
            '_spotlight_fvra_multiple_check_api_client',
            '_iasme_cyber_essentials_api_client',
        ),
    )
    def test_get_status(self, data_insights_api_client, spotlight_client):
        with pytest.raises(NotFound, match='404 Not Found'):
            api_client = getattr(data_insights_api_client, spotlight_client)

            api_client.get_status()


class TestFindOrganisationFromDunsNumber:
    def test_find_organisation_from_duns_number(self, data_insights_api_client, rmock):
        rmock.post(
            'http://data-insights-baseurl/workflows/5319fad3d7e341a89183b32df72671ba/triggers/manual/paths/invoke'
            '?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=api-key',
            json={'searchOrganisation': [{'DunsNumber': '123456789'}]},
            status_code=200,
        )
        result = data_insights_api_client.find_organisation_from_duns_number('123456789')

        assert result == {'organisations': {'DunsNumber': '123456789'}}
        assert rmock.called
        assert rmock.last_request.json() == {
            'requestType': 'SearchOrganisation',
            'parameters': {'dunsNumber': '123456789'},
        }

    def test_find_organisation_from_duns_number_not_found(self, data_insights_api_client, rmock):
        rmock.post(
            'http://data-insights-baseurl/workflows/5319fad3d7e341a89183b32df72671ba/triggers/manual/paths/invoke'
            '?api-version=2016-10-01&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=api-key',
            body=BytesIO(b'The parameters provided are invalid, please use a different combination and try again.'),
            status_code=200,
        )
        try:
            data_insights_api_client.find_organisation_from_duns_number('123456789')
        except HTTPError as e:
            assert rmock.called

            assert e.status_code == 404
            assert e.message == 'Could not find organisation with Duns Number 123456789'


class TestInformSpotlightOfDunsNumberForCheck:
    def test_inform_spotlight_of_duns_number_for_check(self, data_insights_api_client, rmock):
        rmock.post(
            'http://data-insights-baseurl/workflows/91fa768cca7348cab37695fcf34b1262/triggers/Trigger/paths/invoke'
            '?api-version=2016-10-01&sp=%2Ftriggers%2FTrigger%2Frun&sv=1.0&sig=api-key',
            body=BytesIO(b"'Call received.'"),
            status_code=200,
        )
        result = data_insights_api_client.inform_spotlight_of_duns_number_for_check('123456789', 'Vandham')

        assert result == {'message': 'done'}
        assert rmock.called
        assert rmock.last_request.json() == {
            'Account': [
                {'Name': 'Vandham', 'DunsNumber': '123456789', 'OnDemandChecks': 'true', 'PartOfDailyChecks': 'false'}
            ]
        }

    def test_find_organisation_from_duns_number_not_found(self, data_insights_api_client, rmock):
        rmock.post(
            'http://data-insights-baseurl/workflows/91fa768cca7348cab37695fcf34b1262/triggers/Trigger/paths/invoke'
            '?api-version=2016-10-01&sp=%2Ftriggers%2FTrigger%2Frun&sv=1.0&sig=api-key',
            body=BytesIO(b"'Something else'"),
            status_code=200,
        )
        try:
            data_insights_api_client.inform_spotlight_of_duns_number_for_check('123456789', 'Vandham')
        except HTTPError as e:
            assert rmock.called

            assert e.status_code == 500
            assert e.message == 'Could not initiate warm up with Duns Number 123456789'


class TestGetFinancialsFromDunsNumber:
    def test_get_financials_from_duns_number(self, data_insights_api_client, rmock):
        rmock.post(
            'http://data-insights-baseurl/workflows/9f848cc1409f441ca6bae23793ba7960/triggers/Trigger/paths/invoke'
            '?api-version=2016-10-01&sp=%2Ftriggers%2FTrigger%2Frun&sv=1.0&sig=api-key',
            json={
                'ResultSets': [
                    {
                        'DUNS': '123456789',
                        'OrganisationName': 'NLA Corp',
                    }
                ]
            },
            status_code=200,
        )
        result = data_insights_api_client.get_financials_from_duns_number('123456789')

        assert result == {
            'organisationMetrics': {
                'DUNS': '123456789',
                'OrganisationName': 'NLA Corp',
            }
        }
        assert rmock.called
        assert rmock.last_request.json() == {
            'Account': [{'DunsNumber': '123456789', 'OnDemandChecks': 'true', 'PartOfDailyChecks': 'false'}]
        }


class TestGetFinancialsFromDunsNumbers:
    def test_get_financials_from_duns_numbers(self, data_insights_api_client, rmock):
        rmock.post(
            'http://data-insights-baseurl/workflows/6d3d793e151a4a2c86af189bcca435dd/triggers/Trigger/paths/invoke'
            '?api-version=2016-10-01&sp=%2Ftriggers%2FTrigger%2Frun&sv=1.0&sig=api-key',
            json={
                'ResultSets': {
                    'Table1': [
                        {
                            'DUNS': '123456789',
                            'OrganisationName': 'NLA Corp',
                        },
                        {
                            'DUNS': '456789123',
                            'OrganisationName': 'BLADE Corp',
                        },
                    ]
                }
            },
            status_code=200,
        )
        result = data_insights_api_client.get_financials_from_duns_numbers(['123456789', '456789123'])

        assert result == {
            'organisationMetrics': [
                {
                    'DUNS': '123456789',
                    'OrganisationName': 'NLA Corp',
                },
                {
                    'DUNS': '456789123',
                    'OrganisationName': 'BLADE Corp',
                },
            ]
        }
        assert rmock.called
        assert rmock.last_request.json() == {
            'Account': [
                {'DunsNumber': ['123456789', '456789123'], 'OnDemandChecks': 'true', 'PartOfDailyChecks': 'false'}
            ]
        }


class TestGetCyberEssentialsCertificate:
    def test_get_cyber_essentials_certificate(self, data_insights_api_client, rmock):
        rmock.get(
            CERTIFICATE_URL,
            json=[
                {
                    'CompanyName': 'PLUS ULTRA INC.',
                    'CertificateLevel': 'CE+',
                    'CertificateNumber': CERTIFICATE_NUMBER,
                }
            ],
            status_code=200,
        )
        result = data_insights_api_client.get_cyber_essentials_certificate(CERTIFICATE_NUMBER)

        assert result == {
            'cyberEssentialsCertificateDetails': {
                'CompanyName': 'PLUS ULTRA INC.',
                'CertificateLevel': 'CE+',
                'CertificateNumber': CERTIFICATE_NUMBER,
            }
        }
        assert rmock.called
        assert rmock.last_request.headers.get('Authorization') is None

    def test_get_cyber_essentials_certificate_not_found(self, data_insights_api_client, rmock):
        rmock.get(CERTIFICATE_URL, status_code=404)

        with pytest.raises(HTTPError) as e:
            data_insights_api_client.get_cyber_essentials_certificate(CERTIFICATE_NUMBER)

        assert rmock.called
        assert e.value.status_code == 404
        assert e.value.message == f'Could not find cyber essentials certificate with number {CERTIFICATE_NUMBER}'

    def test_get_cyber_essentials_certificate_empty_result_is_not_found(self, data_insights_api_client, rmock):
        rmock.get(CERTIFICATE_URL, json=[], status_code=200)

        with pytest.raises(HTTPError) as e:
            data_insights_api_client.get_cyber_essentials_certificate(CERTIFICATE_NUMBER)

        assert e.value.status_code == 404
        assert e.value.message == f'Could not find cyber essentials certificate with number {CERTIFICATE_NUMBER}'

    @pytest.mark.parametrize(
        'certificate_number',
        (
            '123456789',
            f'{CERTIFICATE_NUMBER} ',
            f"{CERTIFICATE_NUMBER}' or CertificateNumber ne '",
        ),
    )
    def test_certificate_number_that_is_not_a_uuid_is_not_found_without_a_request(
        self, data_insights_api_client, rmock, certificate_number
    ):
        with pytest.raises(HTTPError) as e:
            data_insights_api_client.get_cyber_essentials_certificate(certificate_number)

        assert not rmock.called
        assert e.value.status_code == 404
        assert e.value.message == f'Could not find cyber essentials certificate with number {certificate_number}'


class TestGetCyberEssentialsCertificateWithAnAccessToken:
    def test_get_cyber_essentials_certificate(self, iasme_apim_api_client, rmock):
        rmock.post(TOKEN_URL, json={'access_token': 'access-token', 'expires_in': 3599}, status_code=200)
        rmock.get(
            APIM_CERTIFICATE_URL,
            json=[{'CertificateLevel': 'CE', 'CertificateNumber': CERTIFICATE_NUMBER}],
            status_code=200,
        )

        result = iasme_apim_api_client.get_cyber_essentials_certificate(CERTIFICATE_NUMBER)

        assert result == {
            'cyberEssentialsCertificateDetails': {'CertificateLevel': 'CE', 'CertificateNumber': CERTIFICATE_NUMBER}
        }
        assert parse_qs(rmock.request_history[0].text) == {
            'grant_type': ['client_credentials'],
            'client_id': ['client-id'],
            'client_secret': ['client-secret'],
            'scope': ['api://apim/.default'],
        }
        assert rmock.last_request.headers['Authorization'] == 'Bearer access-token'

    def test_access_token_is_reused_until_shortly_before_it_expires(self, iasme_apim_api_client, rmock):
        token_requests = rmock.post(
            TOKEN_URL,
            [
                {'json': {'access_token': 'first-token', 'expires_in': 3599}, 'status_code': 200},
                {'json': {'access_token': 'second-token', 'expires_in': 3599}, 'status_code': 200},
            ],
        )
        rmock.get(APIM_CERTIFICATE_URL, json=[{'CertificateLevel': 'CE'}], status_code=200)

        with mock.patch('dmapiclient.data_insights.time') as time:
            time.monotonic.return_value = 1000.0
            iasme_apim_api_client.get_cyber_essentials_certificate(CERTIFICATE_NUMBER)
            time.monotonic.return_value = 1000.0 + 3599 - 301
            iasme_apim_api_client.get_cyber_essentials_certificate(CERTIFICATE_NUMBER)

            assert token_requests.call_count == 1
            assert rmock.last_request.headers['Authorization'] == 'Bearer first-token'

            time.monotonic.return_value = 1000.0 + 3599 - 300
            iasme_apim_api_client.get_cyber_essentials_certificate(CERTIFICATE_NUMBER)

        assert token_requests.call_count == 2
        assert rmock.last_request.headers['Authorization'] == 'Bearer second-token'

    def test_access_token_error_stops_the_certificate_request(self, iasme_apim_api_client, rmock):
        rmock.post(TOKEN_URL, json={'error': 'invalid_client'}, status_code=401)
        certificate_requests = rmock.get(APIM_CERTIFICATE_URL, json=[], status_code=200)

        with pytest.raises(HTTPError) as e:
            iasme_apim_api_client.get_cyber_essentials_certificate(CERTIFICATE_NUMBER)

        assert e.value.status_code == 401
        assert not certificate_requests.called

    def test_no_match_response_is_not_found(self, iasme_apim_api_client, rmock):
        rmock.post(TOKEN_URL, json={'access_token': 'access-token', 'expires_in': 3599}, status_code=200)
        rmock.get(APIM_CERTIFICATE_URL, text=NO_MATCH_RESPONSE_TEXT, status_code=400)

        with pytest.raises(HTTPError) as e:
            iasme_apim_api_client.get_cyber_essentials_certificate(CERTIFICATE_NUMBER)

        assert e.value.status_code == 404
        assert e.value.message == f'Could not find cyber essentials certificate with number {CERTIFICATE_NUMBER}'

    def test_other_bad_request_is_not_not_found(self, iasme_apim_api_client, rmock):
        rmock.post(TOKEN_URL, json={'access_token': 'access-token', 'expires_in': 3599}, status_code=200)
        rmock.get(APIM_CERTIFICATE_URL, text='"Something else is wrong"', status_code=400)

        with pytest.raises(HTTPError) as e:
            iasme_apim_api_client.get_cyber_essentials_certificate(CERTIFICATE_NUMBER)

        assert e.value.status_code == 400
