import logging
from datetime import datetime, timezone, timedelta
from enum import Enum
import requests

from .base import BaseAPIClient
from .errors import HTTPError

logger = logging.getLogger(__name__)


class ComplianceURL(Enum):
    GET_SUPPLIER_COMPLIANCE = '/website-data/manual/paths/invoke/[att].[SupplierCertificationChecksDMP]/'


class ComplianceAPIClient(BaseAPIClient):
    """
    API client for harvesting supplier compliance and assurance records
    from Azure APIM / Data Warehouse (CM+ Integration).
    """

    API_VERSION = '2016-10-01'
    SP = '/triggers/manual/run'
    SV = '1.0'
    TOKEN_EXPIRY_MARGIN_SECONDS = 300  # 5-minute proactive buffer before token expiry

    def __init__(
        self,
        base_url=None,
        token_url=None,
        client_id=None,
        client_secret=None,
        scope=None,
        enabled=True,
        timeout=(15, 45),
    ):
        super().__init__(base_url, None, enabled, timeout)
        self._token_url = token_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._scope = scope
        self._auth_token = None
        self._auth_token_expires_at = None

    def init_app(self, app):
        """
        Configure client from Flask application config.
        """
        self._base_url = app.config.get('DM_COMPLIANCE_API_URL', self._base_url)
        self._token_url = app.config.get('DM_COMPLIANCE_TOKEN_URL', self._token_url)
        self._client_id = app.config.get('DM_COMPLIANCE_CLIENT_ID', self._client_id)
        self._client_secret = app.config.get('DM_COMPLIANCE_CLIENT_SECRET', self._client_secret)
        self._scope = app.config.get('DM_COMPLIANCE_TOKEN_SCOPE', self._scope)
        self._enabled = app.config.get('DM_COMPLIANCE_ENABLED', self._enabled)

    def _refresh_auth_token(self):
        """
        Request a new OAuth2 Bearer token from Azure AD using client credentials grant.
        """
        current_time = datetime.now(timezone.utc)

        payload = {
            'grant_type': 'client_credentials',
            'client_id': self._client_id,
            'client_secret': self._client_secret,
            'scope': self._scope,
        }

        try:
            response = self._requests_retry_session(retry_read_timeouts=True).post(
                self._token_url,
                data=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            api_error = HTTPError.create(e)
            logger.warning(
                "API POST request on {api_url} failed with {api_status} '{api_error}'",
                extra={
                    'api_url': self._token_url,
                    'api_status': api_error.status_code,
                    'api_error': str(e),
                },
            )
            raise api_error from e

        token_data = response.json()
        self._auth_token = token_data.get('access_token')
        self._auth_token_expires_at = current_time + timedelta(seconds=int(token_data.get('expires_in', 3600)))

    def _ensure_valid_token(self):
        """
        Check if the cached token is still valid. If expired, missing, or within
        the safety margin of expiring, request a fresh token.
        """
        current_time = datetime.now(timezone.utc)
        if (
            self._auth_token is None
            or self._auth_token_expires_at is None
            or current_time >= (self._auth_token_expires_at - timedelta(seconds=self.TOKEN_EXPIRY_MARGIN_SECONDS))
        ):
            self._refresh_auth_token()

    def get_supplier_compliance(self, dmp_id, framework_number):
        """
        Query Azure APIM for all compliance records across all lots for a given supplier and framework.

        :param dmp_id: DMP Organisation ID (integer or numeric string)
        :param framework_number: Framework agreement code (e.g. 'RM1557.15')
        :return: dict with 'complianceRecords': list of records
        """
        self._ensure_valid_token()

        # Sanitize inputs to prevent OData filter injection
        dmp_id = int(dmp_id)
        framework_number = str(framework_number).strip().replace("'", '')

        params = {
            'api-version': self.API_VERSION,
            'sp': self.SP,
            'sv': self.SV,
            'filter': f"DMPID eq '{dmp_id}' and FrameworkNumber eq '{framework_number}'",
        }

        try:
            response = self._get(ComplianceURL.GET_SUPPLIER_COMPLIANCE.value, params=params)
            return {'complianceRecords': response or []}
        except HTTPError as e:
            response_text = e.response.text.lower() if getattr(e, 'response', None) is not None else ''
            if e.status_code == 404 or (e.status_code == 400 and 'invalid' in response_text):
                logger.info(f'No compliance records found for DMP ID {dmp_id}')
                return {'complianceRecords': []}
            raise e
