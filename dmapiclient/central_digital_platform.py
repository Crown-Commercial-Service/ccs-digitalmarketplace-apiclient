from enum import Enum
import requests
from flask import abort

from . import __version__
from .base import BaseAPIClient, ResponseType


class CentralDigitalPlatformURL(Enum):
    GET_DATA = '/share/data/{sharecode}'
    GET_DOCUMENT = '/share/data/{sharecode}/document/{document_id}'
    # GET_FILE Not used but added for completeness
    GET_FILE = '/share/data/{sharecode}/file'
    # POST_DATA Not used but added for completeness
    POST_DATA = '/share/data'
    POST_DATA_VERIFY = '/share/data/verify'
    GET_ORGANISATION_CODES = '/share/organisations/{organisation_id}/codes'
    # GET_ORGANISATION_SHARE_CODE_DETAILS Not used but added for completeness
    GET_ORGANISATION_SHARE_CODE_DETAILS = '/share/organisations/{organisation_id}/codes/{sharecode}'


class CentralDigitalPlatformAPIClient(BaseAPIClient):
    @property
    def api_key(self):
        return self._api_key

    def __init__(self, base_url=None, api_key=None, enabled=True, timeout=(15, 45,)):
        super().__init__(
            base_url,
            None,
            enabled,
            timeout
        )
        self._api_key = api_key

    def init_app(self, app):
        self._base_url = app.config['DM_CENTRAL_DIGITAL_PLATFORM_API_URL']
        self._api_key = app.config['DM_CENTRAL_DIGITAL_PLATFORM_API_KEY']

    def _get_headers(self):
        return requests.structures.CaseInsensitiveDict({
            "Content-type": "application/json",
            "CDP-Api-Key": self._api_key,
            "User-agent": "DM-API-Client/{}".format(__version__),
        })

    def _get(
        self,
        url,
        params=None,
        *,
        client_wait_for_response: bool = True,
        response_type: ResponseType | None = None,
        **kwargs
    ):
        return self._request(
            "GET",
            url.value.format(**kwargs),
            params=params,
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
            client_wait_for_response=client_wait_for_response,
            response_type=response_type
        )

    def get_status(self):
        abort(404)

    def get_supplier_submitted_information(self, sharecode):
        return self._get(
            CentralDigitalPlatformURL.GET_DATA,
            sharecode=sharecode
        )

    def get_document_within_supplier_submitted_information(self, sharecode, document_id):
        return self._get(
            CentralDigitalPlatformURL.GET_DOCUMENT,
            sharecode=sharecode,
            document_id=document_id,
            response_type=ResponseType.CONTENT,
        )

    def get_supplier_submitted_information_as_file(self, sharecode):
        return self._get(
            CentralDigitalPlatformURL.GET_FILE,
            sharecode=sharecode,
            response_type=ResponseType.CONTENT,
        )

    def verify_shared_data_is_latest_version(self, sharecode, form_version_id):
        return self._post(
            CentralDigitalPlatformURL.POST_DATA_VERIFY,
            data={
                "shareCode": sharecode,
                "formVersionId": form_version_id
            },
        )

    def get_organisation_sharecodes(self, organisation_id):
        return self._get(
            CentralDigitalPlatformURL.GET_ORGANISATION_CODES,
            organisation_id=organisation_id
        )
