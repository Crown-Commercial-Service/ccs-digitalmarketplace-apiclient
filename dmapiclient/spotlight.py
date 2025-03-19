from enum import Enum
import requests
from flask import abort

from . import __version__
from .base import BaseAPIClient, ResponseType
from .errors import HTTPError, InvalidResponse

API_VERSION = '2016-10-01'
SP_DUNS = '/triggers/manual/run'
SP_FVRA = '/triggers/Trigger/run'
SV = '1.0'


class SpotlightAPIError:
    status_code = 404

    def __init__(self, duns_number):
        self.duns_number = duns_number
        self.message = f'Could not find organisation with Duns Number {self.duns_number}'

    def json(self):
        return {
            'error': self.message
        }


class SptlightURL(Enum):
    POST_IDENTITY_SEARCH = '/workflows/5319fad3d7e341a89183b32df72671ba/triggers/manual/paths/invoke'
    POST_FINANCIALS_CHECK = '/workflows/9f848cc1409f441ca6bae23793ba7960/triggers/Trigger/paths/invoke'


class BaseSpotlightAPIClient(BaseAPIClient):
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

    def _get_headers(self):
        return requests.structures.CaseInsensitiveDict({
            "Content-type": "application/json",
            "User-agent": "DM-API-Client/{}".format(__version__),
        })

    def _get_params(self):
        return {
            'api-version': API_VERSION,
            'sp': self.sp,
            'sv': SV,
            'sig': self.api_key
        }

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


class SpotlightDunsAPIClient(BaseSpotlightAPIClient):
    def __init__(self, base_url=None, api_key=None, enabled=True, timeout=(15, 45,)):
        super().__init__(
            SP_DUNS,
            base_url,
            api_key,
            enabled,
            timeout
        )

    def init_app(self, app):
        self._base_url = app.config['DM_SPOTLIGHT_DUNS_API_URL']
        self._api_key = app.config['DM_SPOTLIGHT_DUNS_API_KEY']

    def find_organisation_from_duns_number(self, duns_number):
        try:
            return {
                'organisations': self._post(
                    SptlightURL.POST_IDENTITY_SEARCH,
                    data={
                        "requestType": "SearchOrganisation",
                        "parameters": {
                            "dunsNumber": duns_number
                        }
                    }
                )['searchOrganisation'][0]
            }
        except InvalidResponse as e:
            spotlight_api_error = SpotlightAPIError(duns_number)

            raise HTTPError(spotlight_api_error, spotlight_api_error.message) from e


class SpotlightFvraAPIClient(BaseSpotlightAPIClient):
    def __init__(self, base_url=None, api_key=None, enabled=True, timeout=(15, 45,)):
        super().__init__(
            SP_FVRA,
            base_url,
            api_key,
            enabled,
            timeout
        )

    def init_app(self, app):
        self._base_url = app.config['DM_SPOTLIGHT_FVRA_API_URL']
        self._api_key = app.config['DM_SPOTLIGHT_FVRA_API_KEY']

    def get_financials_from_duns_number(self, duns_number):
        organisation_metrics = self._post(
            SptlightURL.POST_FINANCIALS_CHECK,
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

        if organisation_metrics.get("OrganisationName", "") == "":
            spotlight_api_error = SpotlightAPIError(duns_number)

            raise HTTPError(spotlight_api_error, spotlight_api_error.message)

        return {
            'organisationMetrics': organisation_metrics
        }
