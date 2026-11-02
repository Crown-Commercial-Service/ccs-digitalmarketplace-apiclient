from enum import Enum
import logging
import threading
import time
import requests
from flask import abort

from . import __version__
from .base import BaseAPIClient, ResponseType
from .errors import HTTPError, InvalidResponse
from .exceptions import ImproperlyConfigured

logger = logging.getLogger(__name__)

API_VERSION = '2016-10-01'
SP_DUNS = '/triggers/manual/run'
SP_FVRA = '/triggers/Trigger/run'
SP_IASME = '/triggers/manual/run'
SV = '1.0'
IASME_NO_MATCH_MESSAGE = 'The parameter set you have provided is invalid'
ACCESS_TOKEN_REFRESH_MARGIN_SECONDS = 300


class DataInsightsAPIErrorResponse:
    def __init__(self, number, message):
        self.message = message.format(number=number)

    def json(self):
        return {'error': self.message}


class SpotlightDunsAPIErrorResponse(DataInsightsAPIErrorResponse):
    status_code = 404

    def __init__(self, duns_number):
        super().__init__(duns_number, 'Could not find organisation with Duns Number {number}')


class SpotlightWarmUpAPIErrorResponse(DataInsightsAPIErrorResponse):
    status_code = 500

    def __init__(self, duns_number):
        super().__init__(duns_number, 'Could not initiate warm up with Duns Number {number}')


class IasmeCyberEssentialsAPIErrorResponse(DataInsightsAPIErrorResponse):
    status_code = 404

    def __init__(self, cyber_essentials_certificate_number):
        super().__init__(
            cyber_essentials_certificate_number, 'Could not find cyber essentials certificate with number {number}'
        )


class DataInsightsURL(Enum):
    POST_IDENTITY_SEARCH = '/workflows/5319fad3d7e341a89183b32df72671ba/triggers/manual/paths/invoke'
    POST_FVRA_WARM_UP = '/workflows/91fa768cca7348cab37695fcf34b1262/triggers/Trigger/paths/invoke'
    POST_SINGLE_FINANCIALS_CHECK = '/workflows/9f848cc1409f441ca6bae23793ba7960/triggers/Trigger/paths/invoke'
    POST_MULTIPLE_FINANCIALS_CHECK = '/workflows/6d3d793e151a4a2c86af189bcca435dd/triggers/Trigger/paths/invoke'
    GET_CYBER_ESSENTIALS_CERT = (
        '/workflows/d92a8b97421e4552845c9e6dc0aca5e2/triggers/manual/paths'
        '/invoke/[att].[IASMECyberSecurityCertification]/'
    )
    GET_CYBER_ESSENTIALS_CERT_APIM = '/website-data/manual/paths/invoke/[att].[IASMECyberSecurityCertification]/'


class BaseDataInsightsAPIClient(BaseAPIClient):
    @property
    def api_key(self):
        return self._api_key

    @property
    def sp(self):
        return self._sp

    def __init__(
        self,
        sp,
        base_url=None,
        api_key=None,
        enabled=True,
        timeout=(
            15,
            45,
        ),
    ):
        super().__init__(base_url, None, enabled, timeout)
        self._api_key = api_key
        self._sp = sp

    def init_app(self, base_url, api_key):
        self._base_url = base_url
        self._api_key = api_key

    def _get_headers(self):
        return requests.structures.CaseInsensitiveDict(
            {
                'Content-type': 'application/json',
                'User-agent': 'DM-API-Client/{}'.format(__version__),
            }
        )

    def _get_params(self, params=None):
        return {
            'api-version': API_VERSION,
            'sp': self.sp,
            'sv': SV,
            'sig': self.api_key,
            **(params or {}),
        }

    def _get(
        self,
        url,
        params=None,
        *,
        client_wait_for_response: bool = True,
        response_type: ResponseType | None = None,
        **kwargs,
    ):
        return self._request(
            'GET',
            url,
            params=self._get_params(params),
            client_wait_for_response=client_wait_for_response,
            response_type=response_type,
            **kwargs,
        )

    def _post(
        self, url, data, *, client_wait_for_response: bool = True, response_type: ResponseType | None = None, **kwargs
    ):
        return self._request(
            'POST',
            url,
            data=data,
            params=self._get_params(),
            client_wait_for_response=client_wait_for_response,
            response_type=response_type,
            **kwargs,
        )

    def get_status(self):
        abort(404)


class _SpotlightDunsAPIClient(BaseDataInsightsAPIClient):
    def __init__(
        self,
        base_url=None,
        api_key=None,
        enabled=True,
        timeout=(
            15,
            45,
        ),
    ):
        super().__init__(SP_DUNS, base_url, api_key, enabled, timeout)

    def find_organisation_from_duns_number(self, duns_number):
        try:
            return {
                'organisations': self._post(
                    DataInsightsURL.POST_IDENTITY_SEARCH,
                    data={'requestType': 'SearchOrganisation', 'parameters': {'dunsNumber': duns_number}},
                )['searchOrganisation'][0]
            }
        except InvalidResponse as e:
            spotlight_api_error = SpotlightDunsAPIErrorResponse(duns_number)

            raise HTTPError(spotlight_api_error, spotlight_api_error.message) from e


class _SpotlightFvraWarmUpAPIClient(BaseDataInsightsAPIClient):
    def __init__(
        self,
        base_url=None,
        api_key=None,
        enabled=True,
        timeout=(
            15,
            45,
        ),
    ):
        super().__init__(SP_FVRA, base_url, api_key, enabled, timeout)

    def inform_spotlight_of_duns_number_for_check(self, duns_number, organisation_name):
        response = self._post(
            DataInsightsURL.POST_FVRA_WARM_UP,
            data={
                'Account': [
                    {
                        'Name': organisation_name,
                        'DunsNumber': duns_number,
                        'OnDemandChecks': 'true',
                        'PartOfDailyChecks': 'false',
                    }
                ]
            },
            response_type=ResponseType.CONTENT,
        )

        if response == b"'Call received.'":
            return {'message': 'done'}

        spotlight_api_error = SpotlightWarmUpAPIErrorResponse(duns_number)

        raise HTTPError(spotlight_api_error, spotlight_api_error.message)


class _SpotlightFvraSingleCheckAPIClient(BaseDataInsightsAPIClient):
    def __init__(
        self,
        base_url=None,
        api_key=None,
        enabled=True,
        timeout=(
            15,
            45,
        ),
    ):
        super().__init__(SP_FVRA, base_url, api_key, enabled, timeout)

    def get_financials_from_duns_number(self, duns_number):
        organisation_metrics = self._post(
            DataInsightsURL.POST_SINGLE_FINANCIALS_CHECK,
            data={'Account': [{'DunsNumber': duns_number, 'OnDemandChecks': 'true', 'PartOfDailyChecks': 'false'}]},
        )['ResultSets'][0]

        return {'organisationMetrics': organisation_metrics}


class _SpotlightFvraMultipleCheckAPIClient(BaseDataInsightsAPIClient):
    def __init__(
        self,
        base_url=None,
        api_key=None,
        enabled=True,
        timeout=(
            15,
            45,
        ),
    ):
        super().__init__(SP_FVRA, base_url, api_key, enabled, timeout)

    def get_financials_from_duns_numbers(self, duns_numbers):
        organisation_metrics = self._post(
            DataInsightsURL.POST_MULTIPLE_FINANCIALS_CHECK,
            data={'Account': [{'DunsNumber': duns_numbers, 'OnDemandChecks': 'true', 'PartOfDailyChecks': 'false'}]},
        )['ResultSets']['Table1']

        return {'organisationMetrics': organisation_metrics}


class _IasmeCyberEssentialsAPIClient(BaseDataInsightsAPIClient):
    def __init__(
        self,
        base_url=None,
        api_key=None,
        enabled=True,
        timeout=(
            15,
            45,
        ),
        token_url=None,
        client_id=None,
        client_secret=None,
        scope=None,
    ):
        super().__init__(SP_IASME, base_url, api_key, enabled, timeout)
        self._set_access_token_settings(token_url, client_id, client_secret, scope)

    def init_app(self, base_url, api_key, token_url=None, client_id=None, client_secret=None, scope=None):
        super().init_app(base_url, api_key)
        self._set_access_token_settings(token_url, client_id, client_secret, scope)

    def _set_access_token_settings(self, token_url, client_id, client_secret, scope):
        settings = (token_url, client_id, client_secret, scope)

        if any(settings) and not all(settings):
            raise ImproperlyConfigured(
                f'{self.__class__.__name__} needs the token URL, client ID, client secret and scope together'
            )

        self._token_url = token_url
        self._client_id = client_id
        self._client_secret = client_secret
        self._scope = scope
        self._access_token = None
        self._access_token_refresh_time = 0.0
        self._access_token_lock = threading.Lock()

    @property
    def uses_access_token(self):
        return bool(self._client_id)

    def _get_access_token(self):
        with self._access_token_lock:
            if self._access_token is None or time.monotonic() >= self._access_token_refresh_time:
                self._access_token, self._access_token_refresh_time = self._request_access_token()

            return self._access_token

    def _request_access_token(self):
        requested_time = time.monotonic()

        try:
            response = self._requests_retry_session().post(
                self._token_url,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self._client_id,
                    'client_secret': self._client_secret,
                    'scope': self._scope,
                },
                headers={'User-agent': 'DM-API-Client/{}'.format(__version__)},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            api_error = HTTPError.create(e)
            logger.warning(
                "Access token request on {api_url} failed with {api_status} '{api_error}'",
                extra={
                    'api_url': self._token_url,
                    'api_status': api_error.status_code,
                    'api_error': str(e),
                    'api_time': time.monotonic() - requested_time,
                },
            )
            raise api_error from e

        logger.info(
            'Access token request on {api_url} finished in {api_time}',
            extra={
                'api_url': self._token_url,
                'api_status': response.status_code,
                'api_time': time.monotonic() - requested_time,
            },
        )

        try:
            access_token = response.json()
            return (
                access_token['access_token'],
                requested_time + access_token['expires_in'] - ACCESS_TOKEN_REFRESH_MARGIN_SECONDS,
            )
        except (ValueError, KeyError, TypeError) as e:
            raise InvalidResponse(response, message='Could not read the access token response') from e

    def _get_headers(self):
        headers = super()._get_headers()

        if self.uses_access_token:
            headers['Authorization'] = f'Bearer {self._get_access_token()}'

        return headers

    def _get_params(self, params=None):
        if self.uses_access_token:
            return dict(params or {})

        return super()._get_params(params)

    @staticmethod
    def _is_no_match(e):
        return e.status_code == 400 and IASME_NO_MATCH_MESSAGE in getattr(e.response, 'text', '')

    def get_cyber_essentials_certificate(self, cyber_essentials_certificate_number):
        iasme_api_error = IasmeCyberEssentialsAPIErrorResponse(cyber_essentials_certificate_number)

        if "'" in cyber_essentials_certificate_number:
            raise HTTPError(iasme_api_error, iasme_api_error.message)

        try:
            cyber_essentials_certificates = self._get(
                (
                    DataInsightsURL.GET_CYBER_ESSENTIALS_CERT_APIM
                    if self.uses_access_token
                    else DataInsightsURL.GET_CYBER_ESSENTIALS_CERT
                ),
                params={'Filter': f"CertificateNumber eq '{cyber_essentials_certificate_number}'"},
            )
        except HTTPError as e:
            if e.status_code == 404:
                raise HTTPError(iasme_api_error, iasme_api_error.message) from e

            if self._is_no_match(e):
                logger.warning(
                    "IASME answered 400 '{api_error}' for certificate number {certificate_number}: treated as not found",
                    extra={
                        'api_error': IASME_NO_MATCH_MESSAGE,
                        'certificate_number': cyber_essentials_certificate_number,
                    },
                )
                raise HTTPError(iasme_api_error, iasme_api_error.message) from e

            raise e

        if not cyber_essentials_certificates:
            raise HTTPError(iasme_api_error, iasme_api_error.message)

        return {'cyberEssentialsCertificateDetails': cyber_essentials_certificates[0]}


class DataInsightsAPIClient:
    def __init__(self, **kwargs):
        self._spotlight_duns_api_client = _SpotlightDunsAPIClient(**kwargs.get('spotlight_duns_api_client_kwargs', {}))
        self._spotlight_warm_up_api_client = _SpotlightFvraWarmUpAPIClient(
            **kwargs.get('spotlight_warm_up_api_client_kwargs', {})
        )
        self._spotlight_fvra_single_check_api_client = _SpotlightFvraSingleCheckAPIClient(
            **kwargs.get('spotlight_fvra_single_check_api_client_kwargs', {})
        )
        self._spotlight_fvra_multiple_check_api_client = _SpotlightFvraMultipleCheckAPIClient(
            **kwargs.get('spotlight_fvra_multiple_check_api_client_kwargs', {})
        )
        self._iasme_cyber_essentials_api_client = _IasmeCyberEssentialsAPIClient(
            **kwargs.get('iasme_cyber_essentials_api_client_kwargs', {})
        )

    def init_app(self, app):
        spotlight_api_urls = dict(
            dm_spotlight_api_url.split('=', 1)
            for dm_spotlight_api_url in app.config['DM_DATA_INSIGHTS_API_URLS'].split(',')
        )
        spotlight_api_keys = dict(
            dm_spotlight_api_key.split('=', 1)
            for dm_spotlight_api_key in app.config['DM_DATA_INSIGHTS_API_KEYS'].split(',')
        )
        self._spotlight_duns_api_client.init_app(
            spotlight_api_urls['DM_SPOTLIGHT_DUNS_API_URL'],
            spotlight_api_keys['DM_SPOTLIGHT_DUNS_API_KEY'],
        )
        self._spotlight_warm_up_api_client.init_app(
            spotlight_api_urls['DM_SPOTLIGHT_FVRA_WARM_UP_API_URL'],
            spotlight_api_keys['DM_SPOTLIGHT_FVRA_WARM_UP_API_KEY'],
        )
        self._spotlight_fvra_single_check_api_client.init_app(
            spotlight_api_urls['DM_SPOTLIGHT_FVRA_SINGLE_CHECK_API_URL'],
            spotlight_api_keys['DM_SPOTLIGHT_FVRA_SINGLE_CHECK_API_KEY'],
        )
        self._spotlight_fvra_multiple_check_api_client.init_app(
            spotlight_api_urls['DM_SPOTLIGHT_FVRA_MULTIPLE_CHECK_API_URL'],
            spotlight_api_keys['DM_SPOTLIGHT_FVRA_MULTIPLE_CHECK_API_KEY'],
        )
        self._iasme_cyber_essentials_api_client.init_app(
            spotlight_api_urls['DM_IASME_CYBER_ESSENTIALS_API_URL'],
            spotlight_api_keys['DM_IASME_CYBER_ESSENTIALS_API_KEY'],
            token_url=spotlight_api_urls.get('DM_IASME_CYBER_ESSENTIALS_TOKEN_URL'),
            client_id=spotlight_api_keys.get('DM_IASME_CYBER_ESSENTIALS_CLIENT_ID'),
            client_secret=spotlight_api_keys.get('DM_IASME_CYBER_ESSENTIALS_CLIENT_SECRET'),
            scope=spotlight_api_urls.get('DM_IASME_CYBER_ESSENTIALS_TOKEN_SCOPE'),
        )

    def find_organisation_from_duns_number(self, duns_number):
        return self._spotlight_duns_api_client.find_organisation_from_duns_number(duns_number)

    def inform_spotlight_of_duns_number_for_check(self, duns_number, organisation_name):
        return self._spotlight_warm_up_api_client.inform_spotlight_of_duns_number_for_check(
            duns_number, organisation_name
        )

    def get_financials_from_duns_number(self, duns_number):
        return self._spotlight_fvra_single_check_api_client.get_financials_from_duns_number(duns_number)

    def get_financials_from_duns_numbers(self, duns_numbers):
        return self._spotlight_fvra_multiple_check_api_client.get_financials_from_duns_numbers(duns_numbers)

    def get_cyber_essentials_certificate(self, cyber_essentials_certificate_number):
        return self._iasme_cyber_essentials_api_client.get_cyber_essentials_certificate(
            cyber_essentials_certificate_number
        )
