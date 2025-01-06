import pytest
import mock
from io import BytesIO
from werkzeug.exceptions import NotFound


from dmapiclient import CentralDigitalPlatformAPIClient
from dmapiclient import HTTPError
from dmtestutils.fixtures import valid_pdf_bytes


@pytest.fixture
def cdp_client():
    return CentralDigitalPlatformAPIClient('http://cdp-baseurl', 'api-key', True)


class TestCentralDigitalPlatformApiClient(object):
    def test_base_headers_are_set(self, cdp_client, rmock):
        rmock.request(
            "GET",
            "http://cdp-baseurl/",
            json={},
            status_code=200)

        cdp_client._request('GET', '/')

        assert rmock.last_request.headers.get("Content-type") == "application/json"
        assert rmock.last_request.headers.get("CDP-Api-Key") == "api-key"
        assert rmock.last_request.headers.get("Authorization") is None
        assert rmock.last_request.headers.get("User-Agent").startswith("DM-API-Client/")

    def test_init_app_sets_attributes(self, cdp_client):
        app = mock.Mock()
        app.config = {
            "DM_CENTRAL_DIGITAL_PLATFORM_API_URL": "http://example",
            "DM_CENTRAL_DIGITAL_PLATFORM_API_KEY": "example-api-key",
        }
        cdp_client.init_app(app)

        assert cdp_client.base_url == "http://example"
        assert cdp_client.api_key == "example-api-key"

    def test_get_status(self, cdp_client):
        with pytest.raises(NotFound, match="404 Not Found"):
            cdp_client.get_status()


class TestSupplierInformationMethods(object):
    def test_get_supplier_submitted_information(self, cdp_client, rmock):
        rmock.get(
            "http://cdp-baseurl/share/data/123",
            json={"supplierInformation": "result"},
            status_code=200
        )

        result = cdp_client.get_supplier_submitted_information(123)

        assert result == {"supplierInformation": "result"}
        assert rmock.called

    def test_get_supplier_submitted_information_raises_on_404(self, cdp_client, rmock):
        with pytest.raises(HTTPError):
            rmock.get(
                'http://cdp-baseurl/share/data/123',
                json={'supplierInformation': 'result'},
                status_code=404
            )

            cdp_client.get_supplier_submitted_information(123)

    def test_get_document_within_supplier_submitted_information(self, cdp_client, rmock):
        rmock.get(
            "http://documents-server/123456",
            body=BytesIO(valid_pdf_bytes),
            status_code=200
        )
        rmock.get(
            "http://cdp-baseurl/share/data/123/document/456",
            headers={"location": "http://documents-server/123456"},
            status_code=302
        )

        result = cdp_client.get_document_within_supplier_submitted_information(123, 456)

        assert result == valid_pdf_bytes
        assert rmock.call_count == 2

        assert rmock.request_history[0].method == 'GET'
        assert rmock.request_history[0].url == "http://cdp-baseurl/share/data/123/document/456"
        assert rmock.request_history[1].method
        assert rmock.request_history[1].url == "http://documents-server/123456"

    def test_get_supplier_submitted_information_as_file(self, cdp_client, rmock):
        rmock.get(
            "http://cdp-baseurl/share/data/123/file",
            body=BytesIO(valid_pdf_bytes),
            status_code=200
        )

        result = cdp_client.get_supplier_submitted_information_as_file(123)

        assert result == valid_pdf_bytes
        assert rmock.called


class TestVerifySharedData:
    def test_verify_shared_data_is_latest_version(self, cdp_client, rmock):
        rmock.post(
            "http://cdp-baseurl/share/data/verify",
            json={"is_latest": True},
            status_code=200
        )
        result = cdp_client.verify_shared_data_is_latest_version(123, 456)

        assert result == {"is_latest": True}
        assert rmock.called
        assert rmock.last_request.json() == {
            "shareCode": 123,
            "formVersionId": 456,
        }


class TestOrganisationMethods(object):
    def test_get_organisation_sharecodes(self, cdp_client, rmock):
        rmock.get(
            "http://cdp-baseurl/share/organisations/123/codes",
            json={"sharecodes": "result"},
            status_code=200
        )

        result = cdp_client.get_organisation_sharecodes(123)

        assert result == {"sharecodes": "result"}
        assert rmock.called
