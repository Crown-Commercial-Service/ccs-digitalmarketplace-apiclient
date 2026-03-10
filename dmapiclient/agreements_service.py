from enum import Enum
import requests
from flask import abort

from . import __version__
from .base import BaseAPIClient, ResponseType


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
        enabled=True,
        timeout=(
            15,
            45,
        ),
    ):
        super().__init__(base_url, None, enabled, timeout)
        self._api_key = api_key

    def init_app(self, app):
        self._base_url = app.config['DM_AGREEMENTS_SERVICE_API_URL']
        self._api_key = app.config['DM_AGREEMENTS_SERVICE_API_KEY']

    def _get_headers(self):
        return requests.structures.CaseInsensitiveDict(
            {
                'Content-type': 'application/json',
                'x-api-key': self._api_key,
                'User-agent': 'DM-API-Client/{}'.format(__version__),
            }
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
