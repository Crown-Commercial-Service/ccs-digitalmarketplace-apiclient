import pytest
from unittest import mock
from werkzeug.exceptions import NotFound
from io import BytesIO


from dmapiclient import AgreementsServiceAPIClient


@pytest.fixture
def agreements_service_client():
    return AgreementsServiceAPIClient('http://agreements-service-baseurl', 'api-key', True)


class TestAgreementsServiceAPIClient(object):
    def test_base_headers_are_set(self, agreements_service_client, rmock):
        rmock.request('GET', 'http://agreements-service-baseurl/', json={}, status_code=200)

        agreements_service_client._request('GET', '/')

        assert rmock.last_request.headers.get('Content-type') == 'application/json'
        assert rmock.last_request.headers.get('x-api-key') == 'api-key'
        assert rmock.last_request.headers.get('Authorization') is None
        assert rmock.last_request.headers.get('User-Agent').startswith('DM-API-Client/')

    def test_init_app_sets_attributes(self, agreements_service_client):
        app = mock.Mock()
        app.config = {
            'DM_AGREEMENTS_SERVICE_API_URL': 'http://example',
            'DM_AGREEMENTS_SERVICE_API_KEY': 'example-api-key',
        }
        agreements_service_client.init_app(app)

        assert agreements_service_client.base_url == 'http://example'
        assert agreements_service_client.api_key == 'example-api-key'

    def test_get_status(self, agreements_service_client):
        with pytest.raises(NotFound, match='404 Not Found'):
            agreements_service_client.get_status()


class TestAgreements(object):
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


class TestAgreementLots(object):
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
        rmock.post(
            TestAgreementLots.base_path.format(path=path),
            json={'message': 'done'},
            status_code=200,
        )

    @staticmethod
    def _patch_response_mock(rmock, path):
        rmock.patch(
            TestAgreementLots.base_path.format(path=path),
            body=BytesIO(b''),
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
        assert rmock.request_history[0].json() == {}

    def test_update_agreement_lot_supplier_status_unsuspend(self, agreements_service_client, rmock):
        self._patch_response_mock(rmock, '/suppliers/duns/123456789/status')

        result = agreements_service_client.update_agreement_lot_supplier_status('RM6232', '1a', '123456789', True)

        assert result == b''
        assert rmock.called
        assert rmock.request_history[0].json() == {'operation': 'unsuspend'}

    def test_update_agreement_lot_supplier_status_suspend(self, agreements_service_client, rmock):
        self._patch_response_mock(rmock, '/suppliers/duns/123456789/status')

        result = agreements_service_client.update_agreement_lot_supplier_status('RM6232', '1a', '123456789', False)

        assert result == b''
        assert rmock.called
        assert rmock.request_history[0].json() == {'operation': 'suspend'}


class TestOrganisations(object):
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
        rmock.post(
            TestOrganisations.base_path.format(path=path),
            json={'message': 'done'},
            status_code=200,
        )

    @staticmethod
    def _patch_response_mock(rmock, path):
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
        assert rmock.request_history[0].json() == {
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
        assert rmock.request_history[0].json() == {
            'supplierName': 'Plus Ultra Inc.',
        }

    def test_update_organisation_by_duns_email_address(self, agreements_service_client, rmock):
        self._patch_response_mock(rmock, '/duns/123456789')

        result = agreements_service_client.update_organisation_by_duns('123456789', email_address='email@email.com')

        assert result == b''
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'emailAddress': 'email@email.com',
        }

    def test_update_organisation_by_duns_contact_name(self, agreements_service_client, rmock):
        self._patch_response_mock(rmock, '/duns/123456789')

        result = agreements_service_client.update_organisation_by_duns('123456789', contact_name='Toshinori Yagi')

        assert result == b''
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'contactPointName': 'Toshinori Yagi',
        }

    def test_update_organisation_by_duns_telephone_number(self, agreements_service_client, rmock):
        self._patch_response_mock(rmock, '/duns/123456789')

        result = agreements_service_client.update_organisation_by_duns('123456789', telephone_number='01234567890')

        assert result == b''
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'telephoneNumber': '01234567890',
        }

    def test_update_organisation_by_duns_address_line_1(self, agreements_service_client, rmock):
        self._patch_response_mock(rmock, '/duns/123456789')

        result = agreements_service_client.update_organisation_by_duns('123456789', address_line_1='1 UA High Street')

        assert result == b''
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'streetAddress': '1 UA High Street',
        }

    def test_update_organisation_by_duns_town_or_city(self, agreements_service_client, rmock):
        self._patch_response_mock(rmock, '/duns/123456789')

        result = agreements_service_client.update_organisation_by_duns('123456789', town_or_city='Musutafu')

        assert result == b''
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'locality': 'Musutafu',
        }

    def test_update_organisation_by_duns_postcode(self, agreements_service_client, rmock):
        self._patch_response_mock(rmock, '/duns/123456789')

        result = agreements_service_client.update_organisation_by_duns('123456789', postcode='M1 1AA')

        assert result == b''
        assert rmock.called
        assert rmock.request_history[0].json() == {
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
        assert rmock.request_history[0].json() == {
            'supplierName': 'Plus Ultra Inc.',
            'emailAddress': 'detroit@smash.com',
            'contactPointName': 'Toshinori Yagi',
            'telephoneNumber': '01234567890',
            'streetAddress': '1 UA High Street',
            'locality': 'Musutafu',
            'postalCode': 'M1 1AA',
        }
