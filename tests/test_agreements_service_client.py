import pytest
from werkzeug.exceptions import NotFound
from io import BytesIO


from dmapiclient import AgreementsServiceAPIClient


@pytest.fixture
def agreements_service_client():
    return AgreementsServiceAPIClient(
        'http://agreements-service-baseurl', 'api-key', 'http://access-token-url', 'client-id', 'client-secret', True
    )


class BaseTestAgreementsServiceAPIClient(object):
    @staticmethod
    def mock_refresh_auth_token(rmock, expires_in=3600):
        rmock.post(
            'http://access-token-url',
            json={'access_token': 'ACCESS_TOKEN', 'expires_in': expires_in},
            status_code=200,
        )


class TestAgreementsServiceAPIClient(BaseTestAgreementsServiceAPIClient):
    def test_base_headers_are_set(self, agreements_service_client, rmock):
        self.mock_refresh_auth_token(rmock)
        rmock.request('GET', 'http://agreements-service-baseurl/', json={}, status_code=200)

        agreements_service_client._request('GET', '/')

        assert rmock.last_request.headers.get('Content-type') == 'application/json'
        assert rmock.last_request.headers.get('x-api-key') == 'api-key'
        assert rmock.last_request.headers.get('Authorization') is None
        assert rmock.last_request.headers.get('User-Agent').startswith('DM-API-Client/')

    def test_base_headers_are_set_for_post(self, agreements_service_client, rmock):
        self.mock_refresh_auth_token(rmock)
        rmock.request('POST', 'http://agreements-service-baseurl/', json={}, status_code=200)

        agreements_service_client._request('POST', '/')

        assert rmock.last_request.headers.get('Content-type') == 'application/json'
        assert rmock.last_request.headers.get('x-api-key') == 'api-key'
        assert rmock.last_request.headers.get('Authorization') == 'Bearer ACCESS_TOKEN'
        assert rmock.last_request.headers.get('User-Agent').startswith('DM-API-Client/')

    def test_auth_token_not_fetched_when_get(self, agreements_service_client, rmock):
        self.mock_refresh_auth_token(rmock)
        rmock.request('GET', 'http://agreements-service-baseurl/', json={}, status_code=200)

        agreements_service_client._request('GET', '/')

        assert len(rmock.request_history) == 1

        assert [{'method': request.method, 'url': request.url} for request in rmock.request_history] == [
            {'method': 'GET', 'url': 'http://agreements-service-baseurl/'}
        ]

    @pytest.mark.parametrize(
        'http_method',
        (
            'POST',
            'PATCH',
            'PUT',
            'DELETE',
        ),
    )
    def test_auth_token_fetched_when_not_get(self, agreements_service_client, rmock, http_method):
        self.mock_refresh_auth_token(rmock)
        rmock.request(http_method, 'http://agreements-service-baseurl/', json={}, status_code=200)

        agreements_service_client._request(http_method, '/')

        assert len(rmock.request_history) == 2

        assert [{'method': request.method, 'url': request.url} for request in rmock.request_history] == [
            {'method': 'POST', 'url': 'http://access-token-url/'},
            {'method': http_method, 'url': 'http://agreements-service-baseurl/'},
        ]

    def test_auth_token_fetched_only_once_and_not_on_repeat_requests(self, agreements_service_client, rmock):
        self.mock_refresh_auth_token(rmock)
        rmock.request('POST', 'http://agreements-service-baseurl/', json={}, status_code=200)

        agreements_service_client._request('POST', '/')
        agreements_service_client._request('POST', '/')

        assert len(rmock.request_history) == 3

        assert [{'method': request.method, 'url': request.url} for request in rmock.request_history] == [
            {'method': 'POST', 'url': 'http://access-token-url/'},
            {'method': 'POST', 'url': 'http://agreements-service-baseurl/'},
            {'method': 'POST', 'url': 'http://agreements-service-baseurl/'},
        ]

    def test_auth_token_fetched_again_of_expired(self, agreements_service_client, rmock):
        self.mock_refresh_auth_token(rmock, expires_in=-100)
        rmock.request('POST', 'http://agreements-service-baseurl/', json={}, status_code=200)

        agreements_service_client._request('POST', '/')
        agreements_service_client._request('POST', '/')

        assert len(rmock.request_history) == 4

        assert [{'method': request.method, 'url': request.url} for request in rmock.request_history] == [
            {'method': 'POST', 'url': 'http://access-token-url/'},
            {'method': 'POST', 'url': 'http://agreements-service-baseurl/'},
            {'method': 'POST', 'url': 'http://access-token-url/'},
            {'method': 'POST', 'url': 'http://agreements-service-baseurl/'},
        ]

    def test_get_status(self, agreements_service_client):
        with pytest.raises(NotFound, match='404 Not Found'):
            agreements_service_client.get_status()


class TestAgreements(BaseTestAgreementsServiceAPIClient):
    @staticmethod
    def _get_response_mock(rmock, path, json=None):
        rmock.get(
            f'http://agreements-service-baseurl/agreements-service/agreements{path}',
            json=json if json else {'agreements': 'result'},
            status_code=200,
        )

    def test_find_agreements(self, agreements_service_client, rmock):
        self._get_response_mock(rmock, '')

        result = agreements_service_client.find_agreements()

        assert result == {'agreements': 'result'}
        assert rmock.called

    def test_get_agreement(self, agreements_service_client, rmock):
        self._get_response_mock(rmock, '/RM6232')

        result = agreements_service_client.get_agreement('RM6232')

        assert result == {'agreements': 'result'}
        assert rmock.called

    def test_find_agreement_lots(self, agreements_service_client, rmock):
        self._get_response_mock(rmock, '/RM6232/lots')

        result = agreements_service_client.find_agreement_lots('RM6232')

        assert result == {'agreements': 'result'}
        assert rmock.called

    def test_find_agreement_documents(self, agreements_service_client, rmock):
        self._get_response_mock(rmock, '/RM6232/documents')

        result = agreements_service_client.find_agreement_documents('RM6232')

        assert result == {'agreements': 'result'}
        assert rmock.called

    def test_find_agreement_updates(self, agreements_service_client, rmock):
        self._get_response_mock(rmock, '/RM6232/updates')

        result = agreements_service_client.find_agreement_updates('RM6232')

        assert result == {'agreements': 'result'}
        assert rmock.called


class TestAgreementLots(BaseTestAgreementsServiceAPIClient):
    base_path = 'http://agreements-service-baseurl/agreements-service/agreements/RM6232/lots/1a{path}'

    @staticmethod
    def _get_response_mock(rmock, path, json=None):
        rmock.get(
            TestAgreementLots.base_path.format(path=path),
            json=json if json else {'agreementLots': 'result'},
            status_code=200,
        )

    @staticmethod
    def _post_response_mock(rmock, path):
        TestAgreementLots.mock_refresh_auth_token(rmock)
        rmock.post(
            TestAgreementLots.base_path.format(path=path),
            json={'message': 'done'},
            status_code=200,
        )

    @staticmethod
    def _patch_response_mock(rmock, path):
        TestAgreementLots.mock_refresh_auth_token(rmock)
        rmock.patch(
            TestAgreementLots.base_path.format(path=path),
            body=BytesIO(b''),
            status_code=200,
        )

    @staticmethod
    def _put_response_mock(rmock, path):
        TestAgreementLots.mock_refresh_auth_token(rmock)
        rmock.put(
            TestAgreementLots.base_path.format(path=path),
            json={'message': 'done'},
            status_code=200,
        )

    def test_get_agreement(self, agreements_service_client, rmock):
        self._get_response_mock(rmock, '')

        result = agreements_service_client.get_agreement_lot('RM6232', '1a')

        assert result == {'agreementLots': 'result'}
        assert rmock.called

    def test_find_agreement_lot_suppliers(self, agreements_service_client, rmock):
        self._get_response_mock(rmock, '/suppliers')

        result = agreements_service_client.find_agreement_lot_suppliers('RM6232', '1a')

        assert result == {'agreementLots': 'result'}
        assert rmock.called

    def test_find_agreement_lot_event_types(self, agreements_service_client, rmock):
        self._get_response_mock(rmock, '/event-types')

        result = agreements_service_client.find_agreement_lot_event_types('RM6232', '1a')

        assert result == {'agreementLots': 'result'}
        assert rmock.called

    def test_find_agreement_lot_event_type_data_templates(self, agreements_service_client, rmock):
        self._get_response_mock(rmock, '/event-types/event-name/data-templates')

        result = agreements_service_client.find_agreement_lot_event_type_data_templates('RM6232', '1a', 'event-name')

        assert result == {'agreementLots': 'result'}
        assert rmock.called

    def test_find_agreement_lot_event_type_document_templates(self, agreements_service_client, rmock):
        self._get_response_mock(rmock, '/event-types/event-name/document-templates')

        result = agreements_service_client.find_agreement_lot_event_type_document_templates(
            'RM6232', '1a', 'event-name'
        )

        assert result == {'agreementLots': 'result'}
        assert rmock.called

    def test_create_agreement_lot_supplier(self, agreements_service_client, rmock):
        self._post_response_mock(rmock, '/suppliers/duns/123456789')

        result = agreements_service_client.create_agreement_lot_supplier('RM6232', '1a', '123456789')

        assert result == {'message': 'done'}
        assert rmock.called
        assert rmock.request_history[1].json() == {}

    def test_update_agreement_lot_supplier_details(self, agreements_service_client, rmock):
        self._put_response_mock(rmock, '/suppliers')

        result = agreements_service_client.update_agreement_lot_supplier_details(
            'RM6232',
            '1a',
            'Plus Ultra Inc.',
            '123456789',
            'detroit@smash.com',
            'Toshinori Yagi',
            '01234567890',
            '1 UA High Street',
            'Musutafu',
            'M1 1AA',
            'NP',
            'Japan',
            '2025-12-25',
        )

        assert result == {'message': 'done'}
        assert rmock.called
        assert rmock.request_history[1].json() == [
            {
                'organization': {
                    'identifier': {'legalName': 'Plus Ultra Inc.', 'scheme': 'US-DUNS', 'id': '123456789', 'uri': None},
                    'details': {
                        'creationDate': '2025-12-25',
                        'countryCode': 'NP',
                        'isSme': None,
                        'isVcse': None,
                        'isActive': True,
                    },
                    'address': {
                        'streetAddress': '1 UA High Street',
                        'locality': 'Musutafu',
                        'region': None,
                        'postalCode': 'M1 1AA',
                        'countryName': 'Japan',
                        'countryCode': 'NP',
                    },
                    'contactPoint': {
                        'name': 'Toshinori Yagi',
                        'email': 'detroit@smash.com',
                        'telephone': '01234567890',
                    },
                },
                'supplierStatus': 'ACTIVE',
                'lastUpdatedBy': 'DMP ETL Job',
            }
        ]

    def test_update_agreement_lot_supplier_status_unsuspend(self, agreements_service_client, rmock):
        self._patch_response_mock(rmock, '/suppliers/duns/123456789/status')

        result = agreements_service_client.update_agreement_lot_supplier_status('RM6232', '1a', '123456789', True)

        assert result == b''
        assert rmock.called
        assert rmock.request_history[1].json() == {'operation': 'unsuspend'}

    def test_update_agreement_lot_supplier_status_suspend(self, agreements_service_client, rmock):
        self._patch_response_mock(rmock, '/suppliers/duns/123456789/status')

        result = agreements_service_client.update_agreement_lot_supplier_status('RM6232', '1a', '123456789', False)

        assert result == b''
        assert rmock.called
        assert rmock.request_history[1].json() == {'operation': 'suspend'}


class TestOrganisations(BaseTestAgreementsServiceAPIClient):
    base_path = 'http://agreements-service-baseurl/agreements-service/organisation{path}'

    @staticmethod
    def _get_response_mock(rmock, path, json=None):
        rmock.get(
            TestOrganisations.base_path.format(path=path),
            json=json if json else {'organisations': 'result'},
            status_code=200,
        )

    @staticmethod
    def _post_response_mock(rmock, path):
        TestOrganisations.mock_refresh_auth_token(rmock)
        rmock.post(
            TestOrganisations.base_path.format(path=path),
            json={'message': 'done'},
            status_code=200,
        )

    @staticmethod
    def _patch_response_mock(rmock, path):
        TestOrganisations.mock_refresh_auth_token(rmock)
        rmock.patch(
            TestOrganisations.base_path.format(path=path),
            body=BytesIO(b''),
            status_code=200,
        )

    def test_create_organisation(self, agreements_service_client, rmock):
        self._post_response_mock(rmock, '/suppliers')

        result = agreements_service_client.create_organisation('Plus Ultra Inc.', '123456789', 'NP', 'Japan')

        assert result == {'message': 'done'}
        assert rmock.called
        assert rmock.request_history[1].json() == {
            'legalName': 'Plus Ultra Inc.',
            'registryCode': 'US-DUNS',
            'entityId': '123456789',
            'businessType': None,
            'uri': None,
            'status': 'Active',
            'incorporationDate': '2020-01-01',
            'incorporationCountry': 'NP',
            'countryName': 'Japan',
            'isSme': None,
            'isVcse': None,
            'isActive': True,
        }

    def test_get_organisation_by_name(self, agreements_service_client, rmock):
        self._get_response_mock(rmock, '/identifier/Plus%20Ultra%20INC.')

        result = agreements_service_client.get_organisation_by_name('Plus Ultra INC.')

        assert result == {'organisations': 'result'}
        assert rmock.called

    def test_get_organisation_by_duns(self, agreements_service_client, rmock):
        self._get_response_mock(rmock, '/duns/123456789')

        result = agreements_service_client.get_organisation_by_duns('123456789')

        assert result == {'organisations': 'result'}
        assert rmock.called

    def test_update_organisation_by_duns_supplier_name(self, agreements_service_client, rmock):
        self._patch_response_mock(rmock, '/duns/123456789')

        result = agreements_service_client.update_organisation_by_duns('123456789', supplier_name='Plus Ultra Inc.')

        assert result == b''
        assert rmock.called
        assert rmock.request_history[1].json() == {
            'supplierName': 'Plus Ultra Inc.',
        }

    def test_update_organisation_by_duns_email_address(self, agreements_service_client, rmock):
        self._patch_response_mock(rmock, '/duns/123456789')

        result = agreements_service_client.update_organisation_by_duns('123456789', email_address='email@email.com')

        assert result == b''
        assert rmock.called
        assert rmock.request_history[1].json() == {
            'emailAddress': 'email@email.com',
        }

    def test_update_organisation_by_duns_contact_name(self, agreements_service_client, rmock):
        self._patch_response_mock(rmock, '/duns/123456789')

        result = agreements_service_client.update_organisation_by_duns('123456789', contact_name='Toshinori Yagi')

        assert result == b''
        assert rmock.called
        assert rmock.request_history[1].json() == {
            'contactPointName': 'Toshinori Yagi',
        }

    def test_update_organisation_by_duns_telephone_number(self, agreements_service_client, rmock):
        self._patch_response_mock(rmock, '/duns/123456789')

        result = agreements_service_client.update_organisation_by_duns('123456789', telephone_number='01234567890')

        assert result == b''
        assert rmock.called
        assert rmock.request_history[1].json() == {
            'telephoneNumber': '01234567890',
        }

    def test_update_organisation_by_duns_address_line_1(self, agreements_service_client, rmock):
        self._patch_response_mock(rmock, '/duns/123456789')

        result = agreements_service_client.update_organisation_by_duns('123456789', address_line_1='1 UA High Street')

        assert result == b''
        assert rmock.called
        assert rmock.request_history[1].json() == {
            'streetAddress': '1 UA High Street',
        }

    def test_update_organisation_by_duns_town_or_city(self, agreements_service_client, rmock):
        self._patch_response_mock(rmock, '/duns/123456789')

        result = agreements_service_client.update_organisation_by_duns('123456789', town_or_city='Musutafu')

        assert result == b''
        assert rmock.called
        assert rmock.request_history[1].json() == {
            'locality': 'Musutafu',
        }

    def test_update_organisation_by_duns_postcode(self, agreements_service_client, rmock):
        self._patch_response_mock(rmock, '/duns/123456789')

        result = agreements_service_client.update_organisation_by_duns('123456789', postcode='M1 1AA')

        assert result == b''
        assert rmock.called
        assert rmock.request_history[1].json() == {
            'postalCode': 'M1 1AA',
        }

    def test_update_organisation_by_duns_all_attributes(self, agreements_service_client, rmock):
        self._patch_response_mock(rmock, '/duns/123456789')

        result = agreements_service_client.update_organisation_by_duns(
            '123456789',
            supplier_name='Plus Ultra Inc.',
            email_address='detroit@smash.com',
            contact_name='Toshinori Yagi',
            telephone_number='01234567890',
            address_line_1='1 UA High Street',
            town_or_city='Musutafu',
            postcode='M1 1AA',
        )

        assert result == b''
        assert rmock.called
        assert rmock.request_history[1].json() == {
            'supplierName': 'Plus Ultra Inc.',
            'emailAddress': 'detroit@smash.com',
            'contactPointName': 'Toshinori Yagi',
            'telephoneNumber': '01234567890',
            'streetAddress': '1 UA High Street',
            'locality': 'Musutafu',
            'postalCode': 'M1 1AA',
        }
