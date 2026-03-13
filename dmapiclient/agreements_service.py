import logging
from datetime import datetime, timezone, timedelta

from enum import Enum
import requests
from flask import abort

from . import __version__
from .base import BaseAPIClient, ResponseType
from .errors import HTTPError

logger = logging.getLogger(__name__)


class AgreementsServiceURL(Enum):
    # Agreements endpoints
    FIND_AGREEMENTS = '/agreements-service/agreements'
    GET_AGREEMENT = '/agreements-service/agreements/{agreement_id}'
    FIND_AGREEMENT_LOTS = '/agreements-service/agreements/{agreement_id}/lots'
    FIND_AGREEMENT_DOCUMENTS = '/agreements-service/agreements/{agreement_id}/documents'
    FIND_AGREEMENT_UPDATES = '/agreements-service/agreements/{agreement_id}/updates'

    # Lots API endpoints
    GET_AGREEMENT_LOT = '/agreements-service/agreements/{agreement_id}/lots/{lot_id}'
    FIND_AGREEMENT_LOT_SUPPLIERS = '/agreements-service/agreements/{agreement_id}/lots/{lot_id}/suppliers'
    FIND_AGREEMENT_LOT_EVENT_TYPES = '/agreements-service/agreements/{agreement_id}/lots/{lot_id}/event-types'
    FIND_AGREEMENT_LOT_EVENT_TYPE_DATA_TEMPLATES = (
        '/agreements-service/agreements/{agreement_id}/lots/{lot_id}/event-types/{event_type}/data-templates'
    )
    FIND_AGREEMENT_LOT_EVENT_TYPE_DOCUMENT_TEMPLATES = (
        '/agreements-service/agreements/{agreement_id}/lots/{lot_id}/event-types/{event_type}/document-templates'
    )
    CREATE_AGREEMENT_LOT_SUPPLIER = (
        '/agreements-service/agreements/{agreement_id}/lots/{lot_id}/suppliers/duns/{duns_number}'
    )
    UPDATE_AGREEMENT_LOT_SUPPLIER_DETAILS = '/agreements-service/agreements/{agreement_id}/lots/{lot_id}/suppliers'
    UPDATE_AGREEMENT_LOT_SUPPLIER_STATUS = (
        '/agreements-service/agreements/{agreement_id}/lots/{lot_id}/suppliers/duns/{duns_number}/status'
    )

    # Organisation API endponts
    CREATE_ORGANISATION = '/agreements-service/organisation/suppliers'
    GET_ORGANISATION_BY_NAME = '/agreements-service/organisation/identifier/{organisation_name}'
    GET_ORGANISATION_BY_DUNS = '/agreements-service/organisation/duns/{duns_number}'
    UPDATE_ORGANISATION_BY_DUNS = '/agreements-service/organisation/duns/{duns_number}'


class AgreementsServiceAPIClient(BaseAPIClient):
    @property
    def api_key(self):
        return self._api_key

    def __init__(
        self,
        base_url=None,
        api_key=None,
        access_token_url=None,
        access_token_client_id=None,
        access_token_client_secret=None,
        enabled=True,
        timeout=(
            15,
            45,
        ),
    ):
        super().__init__(base_url, None, enabled, timeout)
        self._api_key = api_key
        self._access_token_url = access_token_url
        self._access_token_client_id = access_token_client_id
        self._access_token_client_secret = access_token_client_secret
        self._auth_token_expires_at = None

    def _get_headers(self):
        base_headers = {
            'Content-type': 'application/json',
            'x-api-key': self._api_key,
            'User-agent': 'DM-API-Client/{}'.format(__version__),
        }
        if self._auth_token is not None:
            base_headers['Authorization'] = 'Bearer {}'.format(self._auth_token)

        return requests.structures.CaseInsensitiveDict(base_headers)

    def _refresh_auth_token(self):
        current_time = datetime.now(timezone.utc)

        try:
            response = self._requests_retry_session(retry_read_timeouts=True).request(
                'POST',
                self._access_token_url,
                auth=(self._access_token_client_id, self._access_token_client_secret),
                data={'grant_type': 'client_credentials'},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as e:
            api_error = HTTPError.create(e)
            logger.log(
                logging.WARNING,
                "API {api_method} request on {api_url} failed with {api_status} '{api_error}'",
                extra={
                    'api_method': 'POST',
                    'api_url': self._access_token_url,
                    'api_status': api_error.status_code,
                    'api_error': '{} raised {}'.format(api_error.message, str(e)),
                },
            )
            raise api_error from e

        token_data = response.json()
        self._auth_token = token_data.get('access_token')
        self._auth_token_expires_at = current_time + timedelta(seconds=token_data.get('expires_in'))

    def _request(  # noqa C901
        self,
        method,
        url,
        data=None,
        params=None,
        *,
        client_wait_for_response: bool = True,
        response_type: ResponseType | None = None,
        **kwargs,
    ):
        if method.upper() != 'GET' and (
            self._auth_token_expires_at is None
            or (self._auth_token_expires_at is not None and datetime.now(timezone.utc) > self._auth_token_expires_at)
        ):
            self._refresh_auth_token()

        return super()._request(
            method,
            url,
            data=data,
            params=params,
            client_wait_for_response=client_wait_for_response,
            response_type=response_type,
            **kwargs,
        )

    def get_status(self):
        abort(404)

    # Agreements endpoints
    def find_agreements(self):
        return self._get(AgreementsServiceURL.FIND_AGREEMENTS)

    def get_agreement(self, agreement_id):
        return self._get(AgreementsServiceURL.GET_AGREEMENT, agreement_id=agreement_id)

    def find_agreement_lots(self, agreement_id):
        return self._get(AgreementsServiceURL.FIND_AGREEMENT_LOTS, agreement_id=agreement_id)

    def find_agreement_documents(self, agreement_id):
        return self._get(AgreementsServiceURL.FIND_AGREEMENT_DOCUMENTS, agreement_id=agreement_id)

    def find_agreement_updates(self, agreement_id):
        return self._get(AgreementsServiceURL.FIND_AGREEMENT_UPDATES, agreement_id=agreement_id)

    # Lots endpoints
    def get_agreement_lot(self, agreement_id, lot_id):
        return self._get(AgreementsServiceURL.GET_AGREEMENT_LOT, agreement_id=agreement_id, lot_id=lot_id)

    def find_agreement_lot_suppliers(self, agreement_id, lot_id):
        return self._get(AgreementsServiceURL.FIND_AGREEMENT_LOT_SUPPLIERS, agreement_id=agreement_id, lot_id=lot_id)

    def find_agreement_lot_event_types(self, agreement_id, lot_id):
        return self._get(AgreementsServiceURL.FIND_AGREEMENT_LOT_EVENT_TYPES, agreement_id=agreement_id, lot_id=lot_id)

    def find_agreement_lot_event_type_data_templates(self, agreement_id, lot_id, event_type):
        return self._get(
            AgreementsServiceURL.FIND_AGREEMENT_LOT_EVENT_TYPE_DATA_TEMPLATES,
            agreement_id=agreement_id,
            lot_id=lot_id,
            event_type=event_type,
        )

    def find_agreement_lot_event_type_document_templates(self, agreement_id, lot_id, event_type):
        return self._get(
            AgreementsServiceURL.FIND_AGREEMENT_LOT_EVENT_TYPE_DOCUMENT_TEMPLATES,
            agreement_id=agreement_id,
            lot_id=lot_id,
            event_type=event_type,
        )

    def create_agreement_lot_supplier(self, agreement_id, lot_id, duns_number):
        return self._post(
            AgreementsServiceURL.CREATE_AGREEMENT_LOT_SUPPLIER,
            {},
            agreement_id=agreement_id,
            lot_id=lot_id,
            duns_number=duns_number,
        )

    def update_agreement_lot_supplier_details(
        self,
        agreement_id,
        lot_id,
        supplier_name,
        duns_number,
        email_address,
        contact_name,
        telephone_number,
        address_line_1,
        town_or_city,
        postcode,
        country_code,
        country_name,
        created_at,
    ):
        return self._put(
            AgreementsServiceURL.UPDATE_AGREEMENT_LOT_SUPPLIER_DETAILS,
            [
                {
                    'organization': {
                        'identifier': {'legalName': supplier_name, 'scheme': 'US-DUNS', 'id': duns_number, 'uri': None},
                        'details': {
                            'creationDate': created_at,
                            'countryCode': country_code,
                            'isSme': None,
                            'isVcse': None,
                            'isActive': True,
                        },
                        'address': {
                            'streetAddress': address_line_1,
                            'locality': town_or_city,
                            'region': None,
                            'postalCode': postcode,
                            'countryName': country_name,
                            'countryCode': country_code,
                        },
                        'contactPoint': {
                            'name': contact_name,
                            'email': email_address,
                            'telephone': telephone_number,
                        },
                    },
                    'supplierStatus': 'ACTIVE',
                    'lastUpdatedBy': 'DMP ETL Job',
                }
            ],
            agreement_id=agreement_id,
            lot_id=lot_id,
        )

    def update_agreement_lot_supplier_status(self, agreement_id, lot_id, duns_number, on_lot):
        status = 'unsuspend' if on_lot else 'suspend'

        return self._patch(
            AgreementsServiceURL.UPDATE_AGREEMENT_LOT_SUPPLIER_STATUS,
            {'operation': status},
            agreement_id=agreement_id,
            lot_id=lot_id,
            duns_number=duns_number,
            response_type=ResponseType.CONTENT,
        )

    # Organisation API endponts
    def create_organisation(self, organisation_name, duns_number, country_code, country_name):
        return self._post(
            AgreementsServiceURL.CREATE_ORGANISATION,
            {
                'legalName': organisation_name,
                'registryCode': 'US-DUNS',
                'entityId': duns_number,
                'businessType': None,
                'uri': None,
                'status': 'Active',
                'incorporationDate': '2020-01-01',
                'incorporationCountry': country_code,
                'countryName': country_name,
                'isSme': None,
                'isVcse': None,
                'isActive': True,
            },
        )

    def get_organisation_by_name(self, organisation_name):
        return self._get(AgreementsServiceURL.GET_ORGANISATION_BY_NAME, organisation_name=organisation_name)

    def get_organisation_by_duns(self, duns_number):
        return self._get(AgreementsServiceURL.GET_ORGANISATION_BY_DUNS, duns_number=duns_number)

    def update_organisation_by_duns(
        self,
        duns_number,
        supplier_name=None,
        email_address=None,
        contact_name=None,
        telephone_number=None,
        address_line_1=None,
        town_or_city=None,
        postcode=None,
    ):
        data = {}

        if supplier_name is not None:
            data['supplierName'] = supplier_name
        if email_address is not None:
            data['emailAddress'] = email_address
        if contact_name is not None:
            data['contactPointName'] = contact_name
        if telephone_number is not None:
            data['telephoneNumber'] = telephone_number
        if address_line_1 is not None:
            data['streetAddress'] = address_line_1
        if town_or_city is not None:
            data['locality'] = town_or_city
        if postcode is not None:
            data['postalCode'] = postcode

        return self._patch(
            AgreementsServiceURL.UPDATE_ORGANISATION_BY_DUNS,
            data,
            duns_number=duns_number,
            response_type=ResponseType.CONTENT,
        )
