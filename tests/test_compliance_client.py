import pytest
from datetime import datetime, timezone, timedelta
from unittest import mock

from dmapiclient import ComplianceAPIClient
from dmapiclient.errors import HTTPError


@pytest.fixture
def compliance_client():
    return ComplianceAPIClient(
        base_url='https://apim.example.com',
        token_url='https://login.microsoftonline.com/example/oauth2/v2.0/token',
        client_id='test-client-id',
        client_secret='test-client-secret',
        scope='api://test/.default',
        enabled=True,
    )


class TestComplianceAPIClient:
    def test_init(self, compliance_client):
        assert compliance_client._base_url == 'https://apim.example.com'
        assert compliance_client._token_url == 'https://login.microsoftonline.com/example/oauth2/v2.0/token'
        assert compliance_client._client_id == 'test-client-id'
        assert compliance_client._client_secret == 'test-client-secret'
        assert compliance_client._scope == 'api://test/.default'
        assert compliance_client._auth_token is None
        assert compliance_client._auth_token_expires_at is None

    def test_init_app_sets_attributes(self, compliance_client):
        app = mock.Mock()
        app.config = {
            'DM_COMPLIANCE_API_URL': 'https://configured-apim.example.com',
            'DM_COMPLIANCE_TOKEN_URL': 'https://configured-token.example.com',
            'DM_COMPLIANCE_CLIENT_ID': 'configured-client-id',
            'DM_COMPLIANCE_CLIENT_SECRET': 'configured-client-secret',
            'DM_COMPLIANCE_TOKEN_SCOPE': 'api://configured/.default',
            'DM_COMPLIANCE_ENABLED': True,
        }

        compliance_client.init_app(app)

        assert compliance_client.base_url == 'https://configured-apim.example.com'
        assert compliance_client._token_url == 'https://configured-token.example.com'
        assert compliance_client._client_id == 'configured-client-id'
        assert compliance_client._client_secret == 'configured-client-secret'
        assert compliance_client._scope == 'api://configured/.default'
        assert compliance_client._enabled is True

    def test_refresh_auth_token_success(self, compliance_client, rmock):
        rmock.post(
            compliance_client._token_url,
            json={'access_token': 'FAKE_TOKEN', 'expires_in': 3600},
            status_code=200,
        )

        compliance_client._refresh_auth_token()

        assert compliance_client._auth_token == 'FAKE_TOKEN'
        assert compliance_client._auth_token_expires_at > datetime.now(timezone.utc)
        assert 'client_id=test-client-id' in rmock.last_request.text
        assert 'client_secret=test-client-secret' in rmock.last_request.text
        assert 'grant_type=client_credentials' in rmock.last_request.text

    def test_refresh_auth_token_raises_on_failure(self, compliance_client, rmock):
        rmock.post(
            compliance_client._token_url,
            text='Unauthorized client',
            status_code=401,
        )

        with pytest.raises(HTTPError) as exc_info:
            compliance_client._refresh_auth_token()

        assert exc_info.value.status_code == 401

    def test_ensure_valid_token_reuses_unexpired_token(self, compliance_client, rmock):
        compliance_client._auth_token = 'EXISTING_TOKEN'
        compliance_client._auth_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        compliance_client._ensure_valid_token()

        assert rmock.called is False
        assert compliance_client._auth_token == 'EXISTING_TOKEN'

    def test_ensure_valid_token_refreshes_when_expired(self, compliance_client, rmock):
        compliance_client._auth_token = 'EXPIRED_TOKEN'
        compliance_client._auth_token_expires_at = datetime.now(timezone.utc) - timedelta(minutes=5)

        rmock.post(
            compliance_client._token_url,
            json={'access_token': 'NEW_TOKEN', 'expires_in': 3600},
            status_code=200,
        )

        compliance_client._ensure_valid_token()

        assert rmock.called is True
        assert compliance_client._auth_token == 'NEW_TOKEN'

    def test_get_supplier_compliance_success(self, compliance_client, rmock):
        compliance_client._auth_token = 'MOCK_TOKEN'
        compliance_client._auth_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        mock_records = [
            {
                'DmpId': 12345,
                'FrameworkNumber': 'RM1557.15',
                'LotNumber': '3',
                'CertificationName': 'Cyber Essentials',
                'RequirementStatus': 'Mandatory',
            }
        ]
        rmock.get(
            'https://apim.example.com/website-data/manual/paths/invoke/%5Batt%5D.%5BSupplierCertificationChecksDMP%5D/',
            complete_qs=False,
            json=mock_records,
            status_code=200,
        )

        response = compliance_client.get_supplier_compliance(dmp_id=12345, framework_number='RM1557.15')

        assert response == {'complianceRecords': mock_records}
        assert rmock.last_request.headers['Authorization'] == 'Bearer MOCK_TOKEN'
        assert rmock.last_request.qs['api-version'] == ['2016-10-01']
        assert rmock.last_request.qs['sp'] == ['/triggers/manual/run']
        assert rmock.last_request.qs['sv'] == ['1.0']
        assert "dmpid eq '12345'" in rmock.last_request.qs['filter'][0].lower()

    def test_get_supplier_compliance_handles_azure_404_not_found(self, compliance_client, rmock):
        compliance_client._auth_token = 'MOCK_TOKEN'
        compliance_client._auth_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        rmock.get(
            'https://apim.example.com/website-data/manual/paths/invoke/%5Batt%5D.%5BSupplierCertificationChecksDMP%5D/',
            complete_qs=False,
            text='The record you have attempted to retrieve is either not present or the parameter set you have provided is invalid, please provide a valid parameter set in order to return results.',
            status_code=404,
        )

        response = compliance_client.get_supplier_compliance(dmp_id=999999, framework_number='RM1557.15')
        assert response == {'complianceRecords': []}

    def test_get_supplier_compliance_handles_legacy_400_as_empty_list(self, compliance_client, rmock):
        compliance_client._auth_token = 'MOCK_TOKEN'
        compliance_client._auth_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        rmock.get(
            'https://apim.example.com/website-data/manual/paths/invoke/%5Batt%5D.%5BSupplierCertificationChecksDMP%5D/',
            complete_qs=False,
            text='The parameter set you have provided is invalid',
            status_code=400,
        )

        response = compliance_client.get_supplier_compliance(dmp_id=999999, framework_number='RM1557.15')
        assert response == {'complianceRecords': []}

    def test_get_supplier_compliance_raises_on_500(self, compliance_client, rmock):
        compliance_client._auth_token = 'MOCK_TOKEN'
        compliance_client._auth_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        rmock.get(
            'https://apim.example.com/website-data/manual/paths/invoke/%5Batt%5D.%5BSupplierCertificationChecksDMP%5D/',
            complete_qs=False,
            text='Internal Server Error',
            status_code=500,
        )

        with pytest.raises(HTTPError) as exc_info:
            compliance_client.get_supplier_compliance(dmp_id=12345, framework_number='RM1557.15')
        assert exc_info.value.status_code == 500

    def test_get_supplier_compliance_raises_value_error_on_invalid_dmp_id(self, compliance_client):
        compliance_client._auth_token = 'MOCK_TOKEN'
        compliance_client._auth_token_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        with pytest.raises(ValueError):
            compliance_client.get_supplier_compliance(dmp_id="invalid' or 1=1 --", framework_number='RM1557.15')
