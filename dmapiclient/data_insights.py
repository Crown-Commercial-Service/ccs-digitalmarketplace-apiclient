from enum import Enum
import requests
from flask import abort

from . import __version__
from .base import BaseAPIClient, ResponseType
from .errors import HTTPError, InvalidResponse

API_VERSION = '2016-10-01'
SP_DUNS = '/triggers/manual/run'
SP_FVRA = '/triggers/Trigger/run'
SP_IASME = '/triggers/manual/run'
SV = '1.0'


class DataInsightsAPIErrorResponse:
    def __init__(self, number, message):
        self.message = message.format(number=number)

    def json(self):
        return {
            'error': self.message
        }


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
            cyber_essentials_certificate_number,
            'Could not find cyber essentials certificate with number {number}'
        )


class DataInsightsURL(Enum):
    POST_IDENTITY_SEARCH = '/workflows/5319fad3d7e341a89183b32df72671ba/triggers/manual/paths/invoke'
    POST_FVRA_WARM_UP = '/workflows/91fa768cca7348cab37695fcf34b1262/triggers/Trigger/paths/invoke'
    POST_SINGLE_FINANCIALS_CHECK = '/workflows/9f848cc1409f441ca6bae23793ba7960/triggers/Trigger/paths/invoke'
    POST_MULTIPLE_FINANCIALS_CHECK = '/workflows/6d3d793e151a4a2c86af189bcca435dd/triggers/Trigger/paths/invoke'
    GET_CYBER_ESSENTIALS_CERT = '/workflows/d92a8b97421e4552845c9e6dc0aca5e2/triggers/manual/paths' \
                                '/invoke/[att].[IASMECyberSecurityCertification]/'


class BaseDataInsightsAPIClient(BaseAPIClient):
    @property
    def api_key(self):
        return self._api_key

    @property
    def sp(self):
        return self._sp

    def __init__(self, sp, base_url=None, api_key=None, enabled=True, timeout=(15, 45,)):
        super().__init__(
            base_url,
            None,
            enabled,
            timeout
        )
        self._api_key = api_key
        self._sp = sp

    def init_app(self, base_url, api_key):
        self._base_url = base_url
        self._api_key = api_key

    def _get_headers(self):
        return requests.structures.CaseInsensitiveDict({
            "Content-type": "application/json",
            "User-agent": "DM-API-Client/{}".format(__version__),
        })

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
        response_type: ResponseType | None = None
    ):
        return self._request(
            "GET",
            url.value,
            params=self._get_params(params),
            client_wait_for_response=client_wait_for_response,
            response_type=response_type
        )

    def _post(
        self,
        url,
        data,
        *,
        client_wait_for_response: bool = True,
        response_type: ResponseType | None = None,
        **kwargs
    ):
        return self._request(
            "POST",
            url.value.format(**kwargs),
            data=data,
            params=self._get_params(),
            client_wait_for_response=client_wait_for_response,
            response_type=response_type
        )

    def get_status(self):
        abort(404)


class _SpotlightDunsAPIClient(BaseDataInsightsAPIClient):
    def __init__(self, base_url=None, api_key=None, enabled=True, timeout=(15, 45,)):
        super().__init__(
            SP_DUNS,
            base_url,
            api_key,
            enabled,
            timeout
        )

    def find_organisation_from_duns_number(self, duns_number):
        try:
            return {
                'organisations': self._post(
                    DataInsightsURL.POST_IDENTITY_SEARCH,
                    data={
                        "requestType": "SearchOrganisation",
                        "parameters": {
                            "dunsNumber": duns_number
                        }
                    }
                )['searchOrganisation'][0]
            }
        except InvalidResponse as e:
            spotlight_api_error = SpotlightDunsAPIErrorResponse(duns_number)

            raise HTTPError(spotlight_api_error, spotlight_api_error.message) from e


class _SpotlightFvraWarmUpAPIClient(BaseDataInsightsAPIClient):
    def __init__(self, base_url=None, api_key=None, enabled=True, timeout=(15, 45,)):
        super().__init__(
            SP_FVRA,
            base_url,
            api_key,
            enabled,
            timeout
        )

    def inform_spotlight_of_duns_number_for_check(self, duns_number, organisation_name):
        response = self._post(
            DataInsightsURL.POST_FVRA_WARM_UP,
            data={
                "Account": [
                    {
                        "Name": organisation_name,
                        "DunsNumber": duns_number,
                        "OnDemandChecks": "true",
                        "PartOfDailyChecks": "false"
                    }
                ]
            },
            response_type=ResponseType.CONTENT
        )

        if response == b"'Call received.'":
            return {
                "message": "done"
            }

        spotlight_api_error = SpotlightWarmUpAPIErrorResponse(duns_number)

        raise HTTPError(spotlight_api_error, spotlight_api_error.message)


class _SpotlightFvraSingleCheckAPIClient(BaseDataInsightsAPIClient):
    def __init__(self, base_url=None, api_key=None, enabled=True, timeout=(15, 45,)):
        super().__init__(
            SP_FVRA,
            base_url,
            api_key,
            enabled,
            timeout
        )

    def get_financials_from_duns_number(self, duns_number):
        organisation_metrics = self._post(
            DataInsightsURL.POST_SINGLE_FINANCIALS_CHECK,
            data={
                "Account": [
                    {
                        "DunsNumber": duns_number,
                        "OnDemandChecks": "true",
                        "PartOfDailyChecks": "false"
                    }
                ]
            }
        )['ResultSets'][0]

        return {
            'organisationMetrics': organisation_metrics
        }


class _SpotlightFvraMultipleCheckAPIClient(BaseDataInsightsAPIClient):
    def __init__(self, base_url=None, api_key=None, enabled=True, timeout=(15, 45,)):
        super().__init__(
            SP_FVRA,
            base_url,
            api_key,
            enabled,
            timeout
        )

    def get_financials_from_duns_numbers(self, duns_numbers):
        organisation_metrics = self._post(
            DataInsightsURL.POST_MULTIPLE_FINANCIALS_CHECK,
            data={
                "Account": [
                    {
                        "DunsNumber": duns_numbers,
                        "OnDemandChecks": "true",
                        "PartOfDailyChecks": "false"
                    }
                ]
            }
        )['ResultSets']['Table1']

        return {
            'organisationMetrics': organisation_metrics
        }


class _IasmeCyberEssentialsAPIClient(BaseDataInsightsAPIClient):
    def __init__(self, base_url=None, api_key=None, enabled=True, timeout=(15, 45,)):
        super().__init__(
            SP_IASME,
            base_url,
            api_key,
            enabled,
            timeout
        )

    def get_cyber_essentials_certificate(self, cyber_essentials_certificate_number):
        try:
            cyber_essentials_certificate_details = self._get(
                DataInsightsURL.GET_CYBER_ESSENTIALS_CERT,
                params={
                    "Filter": f"CertificateNumber eq '{cyber_essentials_certificate_number}'"
                }
            )[0]

            return {
                'cyberEssentialsCertificateDetails': cyber_essentials_certificate_details
            }
        except HTTPError as e:
            if e.status_code == 404:
                iasme_api_error = IasmeCyberEssentialsAPIErrorResponse(cyber_essentials_certificate_number)

                raise HTTPError(iasme_api_error, iasme_api_error.message) from e

            raise e


class DataInsightsAPIClient:
    def __init__(self, **kwargs):
        self._spotlight_duns_api_client = _SpotlightDunsAPIClient(
            **kwargs.get('spotlight_duns_api_client_kwargs', {})
        )
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
            dm_spotlight_api_url.split('=')
            for dm_spotlight_api_url in app.config['DM_DATA_INSIGHTS_API_URLS'].split(',')
        )
        spotlight_api_keys = dict(
            dm_spotlight_api_key.split('=')
            for dm_spotlight_api_key in app.config['DM_DATA_INSIGHTS_API_KEYS'].split(',')
        )
        self._spotlight_duns_api_client.init_app(
            spotlight_api_urls["DM_SPOTLIGHT_DUNS_API_URL"],
            spotlight_api_keys["DM_SPOTLIGHT_DUNS_API_KEY"],
        )
        self._spotlight_warm_up_api_client.init_app(
            spotlight_api_urls["DM_SPOTLIGHT_FVRA_WARM_UP_API_URL"],
            spotlight_api_keys["DM_SPOTLIGHT_FVRA_WARM_UP_API_KEY"],
        )
        self._spotlight_fvra_single_check_api_client.init_app(
            spotlight_api_urls["DM_SPOTLIGHT_FVRA_SINGLE_CHECK_API_URL"],
            spotlight_api_keys["DM_SPOTLIGHT_FVRA_SINGLE_CHECK_API_KEY"],
        )
        self._spotlight_fvra_multiple_check_api_client.init_app(
            spotlight_api_urls["DM_SPOTLIGHT_FVRA_MULTIPLE_CHECK_API_URL"],
            spotlight_api_keys["DM_SPOTLIGHT_FVRA_MULTIPLE_CHECK_API_KEY"],
        )
        self._iasme_cyber_essentials_api_client.init_app(
            spotlight_api_urls["DM_IASME_CYBER_ESSENTIALS_API_URL"],
            spotlight_api_keys["DM_IASME_CYBER_ESSENTIALS_API_KEY"],
        )

    def find_organisation_from_duns_number(self, duns_number):
        return self._spotlight_duns_api_client.find_organisation_from_duns_number(duns_number)

    def inform_spotlight_of_duns_number_for_check(self, duns_number, organisation_name):
        return self._spotlight_warm_up_api_client.inform_spotlight_of_duns_number_for_check(
            duns_number,
            organisation_name
        )

    def get_financials_from_duns_number(self, duns_number):
        return self._spotlight_fvra_single_check_api_client.get_financials_from_duns_number(duns_number)

    def get_financials_from_duns_numbers(self, duns_numbers):
        return self._spotlight_fvra_multiple_check_api_client.get_financials_from_duns_numbers(duns_numbers)

    def get_cyber_essentials_certificate(self, cyber_essentials_certificate_number):
        return self._iasme_cyber_essentials_api_client.get_cyber_essentials_certificate(
            cyber_essentials_certificate_number
        )
