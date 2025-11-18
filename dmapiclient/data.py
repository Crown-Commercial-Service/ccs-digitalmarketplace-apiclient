import warnings
from typing import Dict, Optional

from .audit import AuditTypes
from .base import BaseAPIClient, logger, make_iter_method
from .errors import HTTPError


class DataAPIClient(BaseAPIClient):
    def init_app(self, app):
        self._base_url = app.config['DM_DATA_API_URL']
        self._auth_token = app.config['DM_DATA_API_AUTH_TOKEN']

    # Audit Events

    def find_audit_events(
        self,
        audit_type=None,
        audit_date=None,
        page=None,
        per_page=None,
        acknowledged=None,
        object_type=None,
        object_id=None,
        latest_first=None,
        earliest_for_each_object=None,
        sort_by=None,
        user=None,
        data_supplier_id=None,
        data_framework_slug=None,
    ):
        warnings.warn(
            "The output of 'find_audit_events' is paginated. Use 'find_audit_events_iter' instead.",
            DeprecationWarning
        )

        params = {
            "acknowledged": acknowledged,
            "audit-date": audit_date,
            "data-supplier-id": data_supplier_id,
            "data-framework-slug": data_framework_slug,
            "earliest_for_each_object": earliest_for_each_object,
            "latest_first": latest_first,
            "object-id": object_id,
            "object-type": object_type,
            "page": page,
            "per_page": per_page,
            "sort_by": sort_by,
            "user": user,
        }

        if audit_type:
            if not isinstance(audit_type, AuditTypes):
                raise TypeError("Must be an AuditTypes")
            params["audit-type"] = audit_type.value

        return self._get(
            "/audit-events",
            params=params
        )

    def get_audit_event(self, audit_event_id):
        return self._get(
            "/audit-events/{}".format(audit_event_id)
        )

    find_audit_events_iter = make_iter_method('find_audit_events', 'auditEvents')
    find_audit_events_iter.__name__ = str("find_audit_events_iter")

    def acknowledge_audit_event(self, audit_event_id, user=None):
        return self._post_with_updated_by(
            "/audit-events/{}/acknowledge".format(audit_event_id),
            data={},
            user=user,
        )

    def acknowledge_service_update_including_previous(self, service_id, audit_event_id, user=None):
        return self._post_with_updated_by(
            "/services/{}/updates/acknowledge".format(service_id),
            data={"latestAuditEventId": audit_event_id},
            user=user,
        )

    def create_audit_event(self, audit_type, user=None, data=None, object_type=None, object_id=None):
        if not isinstance(audit_type, AuditTypes):
            raise TypeError("Must be an AuditTypes")
        if data is None:
            data = {}
        payload = {
            "type": audit_type.value,
            "data": data,
        }
        if user is not None:
            payload['user'] = user
        if object_type is not None:
            payload['objectType'] = object_type
        if object_id is not None:
            payload['objectId'] = object_id

        return self._post(
            '/audit-events',
            data={'auditEvents': payload})

    # Suppliers

    def find_suppliers(
        self, prefix=None, page=None, framework=None, duns_number=None, company_registration_number=None, name=None
    ):
        warnings.warn(
            "The output of 'find_suppliers' is paginated. Use 'find_suppliers_iter' instead.",
            DeprecationWarning
        )

        params = {}
        if prefix:
            params["prefix"] = prefix
        if name:
            params["name"] = name
        if page is not None:
            params['page'] = page
        if framework is not None:
            params['framework'] = framework
        if duns_number is not None:
            params['duns_number'] = duns_number
        if company_registration_number is not None:
            params['company_registration_number'] = company_registration_number

        return self._get(
            "/suppliers",
            params=params
        )

    find_suppliers_iter = make_iter_method('find_suppliers', 'suppliers')
    find_suppliers_iter.__name__ = str("find_suppliers_iter")

    def get_supplier(self, supplier_id, with_cdp_supplier_information=None):
        params = {}
        if with_cdp_supplier_information is not None:
            params['with_cdp_supplier_information'] = bool(with_cdp_supplier_information)

        return self._get(
            "/suppliers/{}".format(supplier_id),
            params=params
        )

    def create_supplier(self, supplier):
        return self._post(
            "/suppliers",
            data={"suppliers": supplier},
        )

    def update_supplier(self, supplier_id, supplier, user=None):
        return self._post_with_updated_by(
            "/suppliers/{}".format(supplier_id),
            data={
                "suppliers": supplier,
            },
            user=user,
        )

    def update_contact_information(self, supplier_id, contact_id,
                                   contact, user=None):
        return self._post_with_updated_by(
            "/suppliers/{}/contact-information/{}".format(
                supplier_id, contact_id),
            data={
                "contactInformation": contact,
            },
            user=user,
        )

    def remove_contact_information_personal_data(self, supplier_id, contact_id, user=None):
        return self._post_with_updated_by(
            "/suppliers/{}/contact-information/{}/remove-personal-data".format(supplier_id, contact_id),
            data={},
            user=user,
        )

    def create_central_digital_platform_connection(
        self,
        supplier_id,
        central_digital_platform_data,
        trading_name,
        user=None
    ):
        return self._post_with_updated_by(
            f"/suppliers/{supplier_id}/central-digital-platform/create",
            data={
                "centralDigitalPlatformData": central_digital_platform_data,
                "tradingName": trading_name,
            },
            user=user,
        )

    def revoke_central_digital_platform_connection(self, supplier_id, user=None):
        return self._post_with_updated_by(
            f"/suppliers/{supplier_id}/central-digital-platform/revoke",
            data={},
            user=user,
        )

    def update_supplier_central_digital_platform_data(
        self,
        supplier_id,
        central_digital_platform_data,
        frameworks_to_update=None,
        user=None
    ):
        data = {
            "centralDigitalPlatformData": central_digital_platform_data
        }

        if frameworks_to_update is not None:
            data["frameworksToUpdate"] = frameworks_to_update

        return self._post_with_updated_by(
            f"/suppliers/{supplier_id}/central-digital-platform/update",
            data=data,
            user=user,
        )

    def update_supplier_framework_central_digital_platform_data(
        self,
        supplier_id,
        framework_slug,
        central_digital_platform_data,
        user=None
    ):
        return self._post_with_updated_by(
            f"/suppliers/{supplier_id}/frameworks/{framework_slug}/central-digital-platform/update",
            data={
                "centralDigitalPlatformData": central_digital_platform_data
            },
            user=user,
        )

    def verify_central_digital_platform_organisation(self, central_digital_platform_organisation_id):
        return self._get(
            f"/suppliers/central-digital-platform/verify-organisation/{central_digital_platform_organisation_id}"
        )

    def get_framework_interest(self, supplier_id):
        return self._get(
            "/suppliers/{}/frameworks/interest".format(supplier_id)
        )

    def register_framework_interest(self, supplier_id, framework_slug, user=None):
        return self._put_with_updated_by(
            "/suppliers/{}/frameworks/{}".format(
                supplier_id, framework_slug),
            data={},
            user=user,
        )

    def get_supplier_declaration(self, supplier_id, framework_slug):
        response = self._get(
            "/suppliers/{}/frameworks/{}".format(supplier_id, framework_slug)
        )
        return {'declaration': response['frameworkInterest']['declaration']}

    def set_supplier_declaration(self, supplier_id, framework_slug, declaration, user=None):
        return self._put_with_updated_by(
            "/suppliers/{}/frameworks/{}/declaration".format(supplier_id, framework_slug),
            data={
                "declaration": declaration
            },
            user=user
        )

    def update_supplier_declaration(self, supplier_id, framework_slug, declaration_update, user=None):
        return self._patch_with_updated_by(
            "/suppliers/{}/frameworks/{}/declaration".format(supplier_id, framework_slug),
            data={
                "declaration": declaration_update,
            },
            user=user
        )

    def set_supplier_evaluation_scores(self, supplier_id, framework_slug, lot_slug, evaluation_scores, user=None):
        return self._put_with_updated_by(
            "/suppliers/{}/frameworks/{}/evaluation-scores".format(supplier_id, framework_slug),
            data={
                "lotSlug": lot_slug,
                "evaluationScores": evaluation_scores,
            },
            user=user
        )

    def update_supplier_evaluation_scores(self, supplier_id, framework_slug, lot_slug, evaluation_scores, user=None):
        return self._patch_with_updated_by(
            "/suppliers/{}/frameworks/{}/evaluation-scores".format(supplier_id, framework_slug),
            data={
                "lotSlug": lot_slug,
                "evaluationScores": evaluation_scores,
            },
            user=user
        )

    def remove_supplier_declaration(self, supplier_id, framework_slug, user=None):
        return self._post_with_updated_by(
            "/suppliers/{}/frameworks/{}/declaration".format(
                supplier_id, framework_slug),
            data={},
            user=user
        )

    def get_supplier_fvra(self, supplier_id, framework_slug):
        response = self._get(
            "/suppliers/{}/frameworks/{}".format(supplier_id, framework_slug)
        )
        return {'fvra': response['frameworkInterest']['fvra']}

    def set_supplier_fvra_result(
        self,
        supplier_id,
        framework_slug,
        fvra_route,
        fvra_additional_declaration_answers,
        fvra_results,
        user=None
    ):
        return self._post_with_updated_by(
            "/suppliers/{}/frameworks/{}/set-fvra-result".format(supplier_id, framework_slug),
            data={
                "fvraFrozenResult": {
                    'fvraRoute': fvra_route,
                    'fvraAdditionalDeclarationAnswers': fvra_additional_declaration_answers,
                    'fvraResults': fvra_results,
                }
            },
            user=user
        )

    def update_supplier_fvra(self, supplier_id, framework_slug, fvra_update, user=None):
        return self._patch_with_updated_by(
            "/suppliers/{}/frameworks/{}/fvra".format(supplier_id, framework_slug),
            data={
                "fvra": fvra_update,
            },
            user=user
        )

    def get_supplier_frameworks(
        self,
        supplier_id,
        with_technical_ability_certificates=None,
        with_lot_questions_responses=None,
        with_lot_pricings=None,
    ):
        params = {}

        if with_technical_ability_certificates is not None:
            params['with_technical_ability_certificates'] = bool(with_technical_ability_certificates)
        if with_lot_questions_responses is not None:
            params['with_lot_questions_responses'] = bool(with_lot_questions_responses)
        if with_lot_pricings is not None:
            params['with_lot_pricings'] = bool(with_lot_pricings)

        return self._get(
            "/suppliers/{}/frameworks".format(supplier_id),
            params
        )

    def get_supplier_framework_info(
        self,
        supplier_id,
        framework_slug,
        with_technical_ability_certificates=None,
        with_lot_questions_responses=None,
        with_lot_pricings=None,
        with_cdp_supplier_information=None,
        with_evaluation_scores=None,
    ):
        params = {}

        if with_technical_ability_certificates is not None:
            params['with_technical_ability_certificates'] = bool(with_technical_ability_certificates)
        if with_lot_questions_responses is not None:
            params['with_lot_questions_responses'] = bool(with_lot_questions_responses)
        if with_lot_pricings is not None:
            params['with_lot_pricings'] = bool(with_lot_pricings)
        if with_cdp_supplier_information is not None:
            params['with_cdp_supplier_information'] = bool(with_cdp_supplier_information)
        if with_evaluation_scores is not None:
            params['with_evaluation_scores'] = bool(with_evaluation_scores)

        return self._get(
            "/suppliers/{}/frameworks/{}".format(supplier_id, framework_slug),
            params
        )

    def set_framework_result(self, supplier_id, framework_slug, is_on_framework, user=None):
        return self._post_with_updated_by(
            "/suppliers/{}/frameworks/{}".format(
                supplier_id, framework_slug),
            data={
                "frameworkInterest": {"onFramework": is_on_framework},
            },
            user=user,
        )

    def set_supplier_framework_allow_declaration_reuse(self, supplier_id, framework_slug, allow, user=None):
        return self._post_with_updated_by(
            "/suppliers/{}/frameworks/{}".format(
                supplier_id, framework_slug),
            data={
                "frameworkInterest": {"allowDeclarationReuse": allow},
            },
            user=user,
        )

    def set_supplier_framework_prefill_declaration(
        self,
        supplier_id,
        framework_slug,
        prefill_declaration_from_framework_slug,
        user=None,
    ):
        return self._post_with_updated_by(
            "/suppliers/{}/frameworks/{}".format(
                supplier_id, framework_slug),
            data={
                "frameworkInterest": {"prefillDeclarationFromFrameworkSlug": prefill_declaration_from_framework_slug},
            },
            user=user,
        )

    def set_supplier_framework_application_company_details_confirmed(
        self,
        supplier_id,
        framework_slug,
        application_company_details_confirmed,
        user=None,
    ):
        return self._post_with_updated_by(
            "/suppliers/{}/frameworks/{}".format(
                supplier_id, framework_slug),
            data={
                "frameworkInterest": {"applicationCompanyDetailsConfirmed": application_company_details_confirmed},
            },
            user=user,
        )

    def set_supplier_framework_agreement_version(
        self,
        supplier_id,
        framework_slug,
        agreement_version,
        user=None,
    ):
        return self._post_with_updated_by(
            "/suppliers/{}/frameworks/{}".format(supplier_id, framework_slug),
            data={
                "frameworkInterest": {"agreementVersion": agreement_version},
            },
            user=user,
        )

    def register_framework_agreement_returned(self, supplier_id, framework_slug, user=None, uploader_user_id=None):
        framework_interest_dict = {
            "agreementReturned": True,
        }
        if uploader_user_id is not None:
            framework_interest_dict['agreementDetails'] = {'uploaderUserId': uploader_user_id}

        return self._post_with_updated_by(
            "/suppliers/{}/frameworks/{}".format(
                supplier_id, framework_slug),
            data={"frameworkInterest": framework_interest_dict},
            user=user,
        )

    def unset_framework_agreement_returned(self, supplier_id, framework_slug, user=None):
        return self._post_with_updated_by(
            "/suppliers/{}/frameworks/{}".format(
                supplier_id, framework_slug),
            data={
                "frameworkInterest": {
                    "agreementReturned": False,
                },
            },
            user=user,
        )

    def update_supplier_framework_agreement_details(self, supplier_id, framework_slug, agreement_details, user=None):
        return self._post_with_updated_by(
            "/suppliers/{}/frameworks/{}".format(
                supplier_id, framework_slug),
            data={
                "frameworkInterest": {
                    "agreementDetails": agreement_details
                },
            },
            user=user,
        )

    def register_framework_agreement_countersigned(self, supplier_id, framework_slug, user=None):
        return self._post_with_updated_by(
            "/suppliers/{}/frameworks/{}".format(
                supplier_id, framework_slug),
            data={
                "frameworkInterest": {"countersigned": True},
            },
            user=user,
        )

    def agree_framework_variation(self, supplier_id, framework_slug, variation_slug, agreed_user_id, user=None):
        return self._put_with_updated_by(
            "/suppliers/{}/frameworks/{}/variation/{}".format(
                supplier_id, framework_slug, variation_slug),
            data={
                "agreedVariations": {"agreedUserId": agreed_user_id},
            },
            user=user,
        )

    def find_framework_suppliers(
        self,
        framework_slug,
        agreement_returned=None,
        statuses=None,
        with_declarations=True,
        with_fvra=True,
        with_technical_ability_certificates=None,
        with_lot_questions_responses=None,
        with_lot_pricings=None,
        with_cdp_supplier_information=None,
    ):
        '''
        :param agreement_returned: A boolean value that allows filtering by suppliers who have or have not
                                   returned their framework agreement. If 'agreement_returned' is set then
                                   any value for 'statuses' will be ignored.
        :param statuses: A comma-separated list of the statuses of framework agreements that should be returned.
                         Valid statuses are: signed, on-hold, approved and countersigned.
        :param with_declarations: whether to include declaration data in returned supplierFrameworks
        :param with_technical_ability_certificates: whether to include TAC data
                                                    in returned supplierFrameworks
        :param with_lot_questions_responses: whether to include lot questions responses data
                                             in returned supplierFrameworks
        :param with_lot_pricings: whether to include lot pricings data
                                  in returned supplierFrameworks
        :param with_fvra: whether to include fvra data
                          in returned supplierFrameworks
        :param with_cdp_supplier_information: whether to include CDP supplier information data
                                             in returned supplierFrameworks
        '''
        params = {}
        if agreement_returned is not None:
            params['agreement_returned'] = bool(agreement_returned)
        if statuses is not None:
            params['status'] = statuses
        if with_declarations is not True:
            params['with_declarations'] = bool(with_declarations)
        if with_fvra is not True:
            params['with_fvra'] = bool(with_fvra)
        if with_technical_ability_certificates is not None:
            params['with_technical_ability_certificates'] = bool(with_technical_ability_certificates)
        if with_lot_questions_responses is not None:
            params['with_lot_questions_responses'] = bool(with_lot_questions_responses)
        if with_lot_pricings is not None:
            params['with_lot_pricings'] = bool(with_lot_pricings)
        if with_cdp_supplier_information is not None:
            params['with_cdp_supplier_information'] = bool(with_cdp_supplier_information)
        return self._get(
            '/frameworks/{}/suppliers'.format(framework_slug),
            params=params
        )

    find_framework_suppliers_iter = make_iter_method('find_framework_suppliers', 'supplierFrameworks')
    find_framework_suppliers_iter.__name__ = str("find_framework_suppliers_iter")

    def find_supplier_framework_applications_by_route(
        self,
        framework_slug,
        route,
        evaluation_status=None,
        section_slug=None,
        evaluator_framework_lot_id=None,
        page=None
    ):
        return self._get(
            f"/frameworks/{framework_slug}/suppliers/applications",
            params={
                'route': route,
                'evaluation_status': evaluation_status,
                'section_slug': section_slug,
                'evaluator_framework_lot_id': evaluator_framework_lot_id,
                'page': page
            }
        )

    find_supplier_framework_applications_by_route_iter = make_iter_method(
        'find_supplier_framework_applications_by_route',
        'supplierFrameworks'
    )
    find_supplier_framework_applications_by_route_iter.__name__ = str(
        "find_supplier_framework_applications_by_route_iter"
    )

    def verify_supplier_framework_application(self, framework_slug, supplier_id, lot_slug=None):
        return self._get(
            f"/frameworks/{framework_slug}/suppliers/{supplier_id}/applications/verify",
            params={
                'lot': lot_slug
            }
        )

    def export_suppliers(self, framework_slug, page=None):
        params = {
            'page': page,
        }

        return self._get(f"/suppliers/export/{framework_slug}", params=params)

    export_suppliers_iter = make_iter_method('export_suppliers', 'suppliers')
    export_suppliers_iter.__name__ = str("export_suppliers_iter")

    def migrate_framework_application(self, framework_slug, from_supplier_id, to_supplier_id, user=None):
        return self._post_with_updated_by(
            f"/frameworks/{framework_slug}/migrate-application",
            data={
                'fromSupplierId': from_supplier_id,
                'toSupplierId': to_supplier_id,
            },
            user=user,
        )

    # Users

    def create_user(self, user):
        return self._post(
            "/users",
            data={
                "users": user,
            })

    def find_users(
        self,
        supplier_id=None,
        page=None,
        role=None,
        personal_data_removed=None,
        *,
        user_research_opted_in=None,
        active=None,
    ):
        warnings.warn(
            "The output of 'find_users' is paginated. Use 'find_users_iter' instead.",
            DeprecationWarning
        )

        params = {}
        if supplier_id is not None and role is not None:
            raise ValueError(
                "Cannot get users by both supplier_id and role")
        if supplier_id is not None:
            params['supplier_id'] = supplier_id
        if role is not None:
            params['role'] = role
        if page is not None:
            params['page'] = page
        if personal_data_removed is not None:
            params['personal_data_removed'] = personal_data_removed
        if user_research_opted_in is not None:
            params['user_research_opted_in'] = user_research_opted_in
        if active is not None:
            params['active'] = active
        return self._get("/users", params=params)

    find_users_iter = make_iter_method('find_users', 'users')
    find_users_iter.__name__ = str("find_users_iter")

    def get_user(self, user_id=None, email_address=None):
        if user_id is not None and email_address is not None:
            raise ValueError(
                "Cannot get user by both user_id and email_address")
        elif user_id is not None:
            url = "/users/{}".format(user_id)
            params = {}
        elif email_address is not None:
            url = "/users"
            params = {"email_address": email_address}
        else:
            raise ValueError("Either user_id or email_address must be set")

        try:
            user = self._get(url, params=params)

            if isinstance(user['users'], list):
                user['users'] = user['users'][0]

            return user

        except HTTPError as e:
            if e.status_code != 404:
                raise
        return None

    def authenticate_user(self, email_address, password):
        try:
            response = self._post(
                '/users/auth',
                data={
                    "authUsers": {
                        "emailAddress": email_address,
                        "password": password,
                    }
                })
            return response if response else None
        except HTTPError as e:
            if e.status_code not in [400, 403, 404]:
                raise

    def update_user_password(self, user_id, new_password, updater=None):
        try:
            self._post_with_updated_by(
                '/users/{}'.format(user_id),
                data={
                    "users": {"password": new_password},
                },
                user=updater or self._user or "no logged-in user",
            )
            return True
        except HTTPError:
            return False

    def update_user(self,
                    user_id,
                    locked=None,
                    active=None,
                    role=None,
                    supplier_id=None,
                    name=None,
                    user_research_opted_in=None,
                    updater=None):
        fields = {}
        if locked is not None:
            fields.update({
                'locked': locked
            })

        if active is not None:
            fields.update({
                'active': active
            })

        if user_research_opted_in is not None:
            fields.update({
                'userResearchOptedIn': user_research_opted_in
            })

        if role is not None:
            fields.update({
                'role': role
            })

        if supplier_id is not None:
            fields.update({
                'supplierId': supplier_id
            })

        if name is not None:
            fields.update({
                'name': name
            })

        params = {
            "users": fields,
        }

        user = self._post_with_updated_by(
            '/users/{}'.format(user_id),
            data=params,
            user=updater or self._user or "no logged-in user",
        )

        logger.info("Updated user {user_id} fields {params}",
                    extra={"user_id": user_id, "params": params})
        return user

    def remove_user_personal_data(self, user_id, user=None):
        return self._post_with_updated_by("/users/{}/remove-personal-data".format(user_id), data={}, user=user)

    def export_users(self, framework_slug, page=None):
        params = {
            'page': page,
        }

        return self._get(f"/users/export/{framework_slug}", params=params)

    export_users_iter = make_iter_method('export_users', 'users')
    export_users_iter.__name__ = str("export_users_iter")

    def is_email_address_with_valid_buyer_domain(self, email_address):
        return self._post(
            "/users/check-buyer-email", data={'emailAddress': email_address}
        )['valid']

    def get_buyer_email_domains(self, page=None):
        warnings.warn(
            "The output of 'get_buyer_email_domains' is paginated. Use 'get_buyer_email_domains_iter' instead.",
            DeprecationWarning
        )

        params = {}
        if page is not None:
            params["page"] = page

        return self._get("/buyer-email-domains", params=params)

    get_buyer_email_domains_iter = make_iter_method("get_buyer_email_domains", "buyerEmailDomains")
    get_buyer_email_domains_iter.__name__ = str("get_buyer_email_domains_iter")

    def create_buyer_email_domain(self, buyer_email_domain, user=None):
        return self._post_with_updated_by(
            "/buyer-email-domains",
            data={
                "buyerEmailDomains": {"domainName": buyer_email_domain}
            },
            user=user,
        )

    def delete_buyer_email_domain(self, buyer_email_domain, user=None):
        return self._delete_with_updated_by(
            "/buyer-email-domains",
            data={
                "buyerEmailDomains": {"domainName": buyer_email_domain}
            },
            user=user,
        )

    def email_is_valid_for_admin_user(self, email_address):
        return self._post(
            "/users/valid-admin-email", data={'emailAddress': email_address}
        )['valid']

    # Services

    def find_draft_services(self, supplier_id, service_id=None, framework=None):

        params = {
            'supplier_id': supplier_id
        }
        if service_id is not None:
            params['service_id'] = service_id
        if framework is not None:
            params['framework'] = framework

        return self._get('/draft-services', params=params)

    find_draft_services_iter = make_iter_method('find_draft_services', 'services')
    find_draft_services_iter.__name__ = str("find_draft_services_iter")

    def find_draft_services_by_framework(self, framework_slug, page=None, status=None, supplier_id=None, lot=None):
        warnings.warn(
            "The output of 'find_draft_services_by_framework' is paginated. "
            "Use 'find_draft_services_by_framework_iter' instead.",
            DeprecationWarning
        )

        params = {
            'page': page,
            'status': status,
            'supplier_id': supplier_id,
            'lot': lot
        }

        return self._get('/draft-services/framework/{}'.format(framework_slug), params=params)

    find_draft_services_by_framework_iter = make_iter_method('find_draft_services_by_framework', 'services')
    find_draft_services_by_framework_iter.__name__ = str("find_draft_services_by_framework_iter")

    def get_draft_service(self, draft_id):
        return self._get(
            "/draft-services/{}".format(draft_id)
        )

    def delete_draft_service(self, draft_id, user=None):
        return self._delete_with_updated_by(
            "/draft-services/{}".format(draft_id),
            data={},
            user=user,
        )

    def copy_draft_service_from_existing_service(self, service_id, user=None, data={}):
        return self._put_with_updated_by(
            "/draft-services/copy-from/{}".format(service_id),
            data=data,
            user=user,
        )

    def copy_published_from_framework(self, framework_slug, lot_slug, user=None, data={}):
        return self._post_with_updated_by(
            "/draft-services/{}/{}/copy-published-from-framework".format(framework_slug, lot_slug),
            data=data,
            user=user,
        )

    def copy_draft_service(self, draft_id, user=None):
        return self._post_with_updated_by(
            "/draft-services/{}/copy".format(draft_id),
            data={},
            user=user,
        )

    def update_draft_service(self, draft_id, service, user=None, page_questions=None, ignored_fields=None):
        data = {
            "services": service,
        }

        if page_questions is not None:
            data['page_questions'] = page_questions

        if ignored_fields is not None:
            data['ignored_fields'] = ignored_fields

        return self._post_with_updated_by("/draft-services/{}".format(draft_id), data=data, user=user)

    def validate_draft_service(self, draft_id, service, page_questions=None, ignored_fields=None):
        data = {
            "services": service,
        }

        if page_questions is not None:
            data['page_questions'] = page_questions

        if ignored_fields is not None:
            data['ignored_fields'] = ignored_fields

        return self._post("/draft-services/{}/validate".format(draft_id), data=data)

    def complete_draft_service(self, draft_id, user=None):
        return self._post_with_updated_by(
            "/draft-services/{}/complete".format(draft_id),
            data={},
            user=user,
        )

    def update_draft_service_status(self, draft_id, status, user=None):
        data = {
            "services": {"status": status},
        }

        return self._post_with_updated_by(
            "/draft-services/{}/update-status".format(draft_id),
            data=data,
            user=user,
        )

    def publish_draft_service(self, draft_id, user=None):
        return self._post_with_updated_by(
            "/draft-services/{}/publish".format(draft_id),
            data={},
            user=user,
        )

    def create_new_draft_service(self, framework_slug, lot, supplier_id, data, user=None, page_questions=None):
        service_data = data.copy()
        service_data.update({
            "frameworkSlug": framework_slug,
            "lot": lot,
            "supplierId": supplier_id,
        })

        return self._post_with_updated_by(
            "/draft-services",
            data={
                "services": service_data,
                "page_questions": page_questions or [],
            },
            user=user,
        )

    def get_archived_service(self, archived_service_id):
        return self._get("/archived-services/{}".format(archived_service_id))

    def get_service(self, service_id, with_pending_data=None):
        try:
            return self._get(
                "/services/{}".format(service_id),
                params={
                    'with_pending_data': with_pending_data
                }
            )
        except HTTPError as e:
            if e.status_code != 404:
                raise
        return None

    def find_services(self, supplier_id=None, framework=None, status=None, page=None, lot=None):
        """
        The response will be paginated unless you provide supplier_id.
        """
        warnings.warn(
            "The output of 'find_services' is paginated. Use 'find_services_iter' instead.",
            DeprecationWarning
        )

        params = {
            'supplier_id': supplier_id,
            'framework': framework,
            'lot': lot,
            'status': status,
            'page': page,
        }

        return self._get("/services", params=params)

    find_services_iter = make_iter_method('find_services', 'services')
    find_services_iter.__name__ = str("find_services_iter")

    def update_service(self, service_id, service, user=None, user_role='', *, wait_for_index: bool = True):
        return self._post_with_updated_by(
            "/services/{}?{}{}".format(
                service_id,
                "&wait-for-index={}".format(str(wait_for_index).lower()),
                "&user-role={}".format(user_role) if user_role else "",
            ),
            data={
                "services": service,
            },
            user=user,
        )

    def update_pending_service(self, service_id, service, user=None):
        return self._post_with_updated_by(
            f"/pending-services/{service_id}",
            data={
                "services": service,
            },
            user=user,
        )

    def approve_pending_service(self, service_id, user=None):
        return self._post_with_updated_by(
            f"/pending-services/{service_id}/approve",
            data={},
            user=user,
        )

    def reject_pending_service(self, service_id, reason_code, reason_text, user=None):
        return self._post_with_updated_by(
            f"/pending-services/{service_id}/reject",
            data={
                "reasonCode": reason_code,
                "reasonText": reason_text,
            },
            user=user,
        )

    def update_service_status(self, service_id, status, user=None, *, wait_for_index: bool = True):
        return self._post_with_updated_by(
            "/services/{}/status/{}{}".format(
                service_id,
                status,
                "?wait-for-index={}".format(str(wait_for_index).lower()),
            ),
            data={},
            user=user,
        )

    def revert_service(self, service_id, archived_service_id, user=None):
        return self._post_with_updated_by(
            "/services/{}/revert".format(service_id),
            data={"archivedServiceId": int(archived_service_id)},
            user=user,
        )

    def find_frameworks(self):
        return self._get("/frameworks")

    def get_framework(self, slug):
        return self._get("/frameworks/{}".format(slug))

    def create_framework(
        self,
        slug,
        name,
        framework_family_slug,
        lots,
        has_direct_award,
        has_further_competition,
        fvra_settings,
        evaluation_settings,
        technical_ability_certificate_settings,
        lot_pricing_settings,
        user=None,
        *,
        status="coming",
        clarification_questions_open=False
    ):
        framework_data = {
            "slug": slug,
            "name": name,
            "framework": framework_family_slug,
            "status": status,
            "clarificationQuestionsOpen": clarification_questions_open,
            "lots": lots,
            "hasDirectAward": has_direct_award,
            "hasFurtherCompetition": has_further_competition,
            "fvraSettings": fvra_settings,
            "evaluationSettings": evaluation_settings,
            "technicalAbilityCertificateSettings": technical_ability_certificate_settings,
            "lotPricingSettings": lot_pricing_settings,
        }

        return self._post_with_updated_by(
            "/frameworks",
            data={"frameworks": framework_data},
            user=user
        )

    def update_framework(self, framework_slug, data, user=None):
        return self._post_with_updated_by(
            "/frameworks/{}".format(framework_slug),
            data={"frameworks": data},
            user=user
        )

    def transition_dos_framework(self, framework_slug, expiring_framework_slug, user=None):
        return self._post_with_updated_by(
            "/frameworks/transition-dos/{}".format(framework_slug),
            data={"expiringFramework": expiring_framework_slug},
            user=user,
        )

    def get_interested_suppliers(self, framework_slug):
        return self._get(
            "/frameworks/{}/interest".format(framework_slug)
        )

    def get_framework_stats(self, framework_slug):
        return self._get(
            "/frameworks/{}/stats".format(framework_slug))

    def update_framework_communication_category(self, framework_slug, data, user=None):
        return self._post_with_updated_by(
            f"/frameworks/{framework_slug}/communication-category",
            data={"communicationCategories": data},
            user=user
        )

    def delete_framework_communication_category(self, framework_slug, communication_category, user=None):
        return self._delete_with_updated_by(
            f"/frameworks/{framework_slug}/communication-category",
            data={"communicationCategory": communication_category},
            user=user
        )

    # Buyer briefs

    def create_brief(self, framework_slug, lot_slug, user_id, data, updated_by=None, page_questions=None):
        brief_data = data.copy()
        brief_data.update({
            "frameworkSlug": framework_slug,
            "lot": lot_slug,
            "userId": user_id,
        })
        return self._post_with_updated_by(
            "/briefs",
            data={
                "briefs": brief_data,
                "page_questions": page_questions or [],
            },
            user=updated_by,
        )

    def copy_brief(self, brief_id, updated_by=None):
        return self._post_with_updated_by(
            "/briefs/{}/copy".format(brief_id),
            data={},
            user=updated_by,
        )

    def update_brief(self, brief_id, brief, updated_by=None, page_questions=None):
        return self._post_with_updated_by(
            "/briefs/{}".format(brief_id),
            data={
                "briefs": brief,
                "page_questions": page_questions or [],
            },
            user=updated_by,
        )

    def update_brief_award_brief_response(self, brief_id, brief_response_id, updated_by=None):
        return self._post_with_updated_by(
            "/briefs/{}/award".format(brief_id),
            data={"briefResponseId": brief_response_id},
            user=updated_by,
        )

    def update_brief_award_details(self, brief_id, brief_response_id, award_details, updated_by=None):
        return self._post_with_updated_by(
            "/briefs/{}/award/{}/contract-details".format(brief_id, brief_response_id),
            data={"awardDetails": award_details},
            user=updated_by,
        )

    def unaward_brief_response(self, brief_id, brief_response_id, updated_by=None):
        return self._delete_with_updated_by(
            f"/briefs/{brief_id}/award/{brief_response_id}/contract-details",
            data={},
            user=updated_by,
        )

    def publish_brief(self, brief_id, user=None):
        return self._post_with_updated_by(
            "/briefs/{}/publish".format(brief_id),
            data={},
            user=user,
        )

    def cancel_brief(self, brief_id, user=None):
        return self._post_with_updated_by(
            "/briefs/{}/cancel".format(brief_id),
            data={},
            user=user,
        )

    def withdraw_brief(self, brief_id, user=None):
        return self._post_with_updated_by(
            "/briefs/{}/withdraw".format(brief_id),
            data={},
            user=user,
        )

    def update_brief_as_unsuccessful(self, brief_id, user=None):
        return self._post_with_updated_by(
            "/briefs/{}/unsuccessful".format(brief_id),
            data={},
            user=user,
        )

    def get_brief(self, brief_id):
        return self._get(
            "/briefs/{}".format(brief_id))

    def find_briefs(
        self, user_id=None, status=None, framework=None, lot=None, page=None, human=None, with_users=None,
        with_clarification_questions=None, closed_on=None, withdrawn_on=None, cancelled_on=None, unsuccessful_on=None,
        status_date_filters: Optional[Dict[str, str]] = None,
    ):
        """
        The response will be paginated unless you provide user_id.

        :param status_date_filters: contains additional status date filters. For permitted keys, see `list_briefs` in
        https://github.com/alphagov/digitalmarketplace-api/blob/main/app/main/views/briefs.py
        """
        warnings.warn(
            "The output of 'find_briefs' is paginated. Use 'find_briefs_iter' instead.",
            DeprecationWarning
        )

        params = {
            "user_id": user_id,
            "framework": framework,
            "lot": lot,
            "status": status,
            "page": page,
            "human": human,
            "with_users": with_users,
            "with_clarification_questions": with_clarification_questions,
            "closed_on": closed_on,
            "withdrawn_on": withdrawn_on,
            "cancelled_on": cancelled_on,
            "unsuccessful_on": unsuccessful_on
        }

        if status_date_filters:
            params.update(status_date_filters)

        return self._get(
            "/briefs",
            params=params
        )

    find_briefs_iter = make_iter_method('find_briefs', 'briefs')
    find_briefs_iter.__name__ = str("find_briefs_iter")

    def delete_brief(self, brief_id, user=None):
        return self._delete_with_updated_by(
            "/briefs/{}".format(brief_id),
            data={},
            user=user,
        )

    def is_supplier_eligible_for_brief(self, supplier_id, brief_id):
        return len(self._get(
            "/briefs/{}/services".format(brief_id),
            params={"supplier_id": supplier_id}
        )['services']) > 0

    def create_brief_response(self, brief_id, supplier_id, data, user=None, page_questions=None):
        data = dict(data, briefId=brief_id, supplierId=supplier_id)
        return self._post_with_updated_by(
            "/brief-responses",
            data={
                "briefResponses": data,
                "page_questions": page_questions or [],
            },
            user=user,
        )

    def update_brief_response(self, brief_response_id, data, user=None, page_questions=None):
        return self._post_with_updated_by(
            "/brief-responses/{}".format(brief_response_id),
            data={
                "briefResponses": data,
                "page_questions": page_questions or [],
            },
            user=user,
        )

    def submit_brief_response(self, brief_response_id, user=None):
        return self._post_with_updated_by(
            "/brief-responses/{}/submit".format(brief_response_id),
            data={},
            user=user,
        )

    def get_brief_response(self, brief_response_id):
        return self._get(
            "/brief-responses/{}".format(brief_response_id))

    def find_brief_responses(
        self,
        brief_id=None,
        supplier_id=None,
        status=None,
        framework=None,
        awarded_at=None,
        *,
        with_data: Optional[bool] = None,
    ):
        """
        The response will be paginated unless you provide supplier_id or brief_id.
        """
        return self._get(
            "/brief-responses",
            params={
                "brief_id": brief_id,
                "supplier_id": supplier_id,
                "status": status,
                "framework": framework,
                "awarded_at": awarded_at,
                "with-data": str(with_data).lower() if with_data is not None else None,
            })

    find_brief_responses_iter = make_iter_method('find_brief_responses', 'briefResponses')
    find_brief_responses_iter.__name__ = str("find_brief_responses_iter")

    def add_brief_clarification_question(self, brief_id, question, answer, user=None):
        return self._post_with_updated_by(
            "/briefs/{}/clarification-questions".format(brief_id),
            data={
                "clarificationQuestion": {
                    "question": question,
                    "answer": answer,
                }
            },
            user=user)

    # Agreements

    def get_framework_agreement(self, framework_agreement_id):
        return self._get(
            "/agreements/{}".format(framework_agreement_id))

    def get_supplier_framework_agreement(self, framework_slug):
        return self._get(
            "/agreements/{}".format(framework_slug))

    def create_framework_agreement(self, supplier_id, framework_slug, signed_agreement_details, user=None):
        return self._post_with_updated_by(
            "/agreements",
            data={
                "agreement": {
                    "supplierId": supplier_id,
                    "frameworkSlug": framework_slug,
                    "signedAgreementDetails": signed_agreement_details
                },
            },
            user=user
        )

    def update_framework_agreement(self, framework_agreement_id, framework_agreement, user=None):
        return self._post_with_updated_by(
            "/agreements/{}".format(framework_agreement_id),
            data={
                "agreement": framework_agreement,
            },
            user=user,
        )

    def update_framework_agreement_undo_countersign(self, framework_agreement_id, user=None):
        return self._post_with_updated_by(
            "/agreements/{}/undo-countersign".format(framework_agreement_id),
            data={},
            user=user,
        )

    def sign_framework_agreement(self, framework_agreement_id, user, signed_agreement_details=None):
        data = {"agreement": {"signedAgreementDetails": signed_agreement_details}} if signed_agreement_details else {}
        return self._post_with_updated_by(
            "/agreements/{}/sign".format(framework_agreement_id),
            data=data,
            user=user,
        )

    def put_signed_agreement_on_hold(self, framework_agreement_id, user):
        return self._post_with_updated_by(
            "/agreements/{}/on-hold".format(framework_agreement_id),
            data={},
            user=user
        )

    def approve_agreement_for_countersignature(self, framework_agreement_id, user, user_id):
        return self._post_with_updated_by(
            "/agreements/{}/approve".format(framework_agreement_id),
            data={
                "agreement": {"userId": user_id}
            },
            user=user
        )

    def unapprove_agreement_for_countersignature(self, framework_agreement_id, user, user_id):
        return self._post_with_updated_by(
            "/agreements/{}/approve".format(framework_agreement_id),
            data={
                "agreement": {
                    "userId": user_id,
                    "unapprove": True,
                },
            },
            user=user
        )

    # Direct Award Projects

    def find_direct_award_projects(
        self,
        user_id=None,
        having_outcome=None,
        locked=None,
        page=None,
        latest_first=None,
        with_users=False,
    ):
        warnings.warn(
            "The output of 'find_direct_award_projects' is paginated. Use 'find_direct_award_projects_iter' instead.",
            DeprecationWarning
        )

        params = {
            "user-id": user_id,
            "page": page,
        }

        if latest_first is not None:
            params['latest-first'] = latest_first
        if having_outcome is not None:
            params['having-outcome'] = having_outcome
        if locked is not None:
            params['locked'] = locked
        if with_users:
            params['include'] = "users"

        return self._get(
            "/direct-award/projects",
            params=params,
        )

    find_direct_award_projects_iter = make_iter_method('find_direct_award_projects', 'projects')
    find_direct_award_projects_iter.__name__ = str("find_direct_award_projects_iter")

    def get_direct_award_project(self, project_id):
        return self._get("/direct-award/projects/{}".format(project_id))

    def create_direct_award_project(self, user_id, user_email, project_name):
        return self._post_with_updated_by(
            "/direct-award/projects",
            data={
                "project": {
                    "name": project_name,
                    "userId": user_id
                }
            },
            user=user_email
        )

    def find_direct_award_project_searches(self, project_id, user_id=None, page=None, only_active=None):
        warnings.warn(
            "The output of 'find_direct_award_project_searches' is paginated. "
            "Use 'find_direct_award_project_searches_iter' instead.",
            DeprecationWarning
        )

        params = {
            "user-id": user_id,
            "page": page,
        }

        if only_active is not None:
            params.update({'only-active': only_active})

        return self._get(
            "/direct-award/projects/{}/searches".format(project_id),
            params=params
        )

    find_direct_award_project_searches_iter = make_iter_method('find_direct_award_project_searches', 'searches')
    find_direct_award_project_searches_iter.__name__ = str("find_direct_award_project_searches_iter")

    def create_direct_award_project_search(self, user_id, user_email, project_id, search_url):
        return self._post_with_updated_by(
            "/direct-award/projects/{}/searches".format(project_id),
            data={
                "search": {
                    "searchUrl": search_url,
                    "userId": user_id
                }
            },
            user=user_email
        )

    def get_direct_award_project_search(self, user_id, project_id, search_id):
        return self._get(
            "/direct-award/projects/{}/searches/{}".format(project_id, search_id),
            params={
                "user-id": user_id
            }
        )

    def find_direct_award_project_services(self, project_id, user_id=None, fields=[]):
        params = {"user-id": user_id}
        if fields:
            params.update({"fields": ','.join(fields)})

        return self._get(
            "/direct-award/projects/{}/services".format(project_id),
            params=params
        )

    find_direct_award_project_services_iter = make_iter_method('find_direct_award_project_services', 'services')
    find_direct_award_project_services_iter.__name__ = str("find_direct_award_project_services_iter")

    def lock_direct_award_project(self, user_email, project_id):
        return self._post_with_updated_by(
            "/direct-award/projects/{}/lock".format(project_id),
            data={},
            user=user_email,
        )

    def record_direct_award_project_download(self, user_email, project_id):
        return self._post_with_updated_by(
            "/direct-award/projects/{}/record-download".format(project_id),
            data={},
            user=user_email,
        )

    def create_direct_award_project_outcome_award(self, project_id, awarded_service_id, user_email):
        return self._post_with_updated_by(
            "/direct-award/projects/{}/services/{}/award".format(project_id, awarded_service_id),
            data={},
            user=user_email,
        )

    def create_direct_award_project_outcome_cancelled(self, project_id, user_email):
        return self._post_with_updated_by(
            "/direct-award/projects/{}/cancel".format(project_id),
            data={},
            user=user_email,
        )

    def create_direct_award_project_outcome_none_suitable(self, project_id, user_email):
        return self._post_with_updated_by(
            "/direct-award/projects/{}/none-suitable".format(project_id),
            data={},
            user=user_email,
        )

    def mark_direct_award_project_as_still_assessing(self, project_id, user_email):
        return self._patch_with_updated_by(
            f"/direct-award/projects/{project_id}",
            data={"project": {"stillAssessing": True}},
            user=user_email,
        )

    def update_direct_award_project(self, project_id, project_data, user_email):
        return self._patch_with_updated_by(
            f"/direct-award/projects/{project_id}",
            data={"project": project_data},
            user=user_email,
        )

    # Outcomes

    def update_outcome(self, outcome_id, outcome_data, user_email):
        return self._put_with_updated_by(
            "/outcomes/{}".format(outcome_id),
            data={
                "outcome": outcome_data,
            },
            user=user_email,
        )

    def get_outcome(self, outcome_id):
        return self._get("/outcomes/{}".format(outcome_id))

    def find_outcomes(self, completed=None, page=None):
        warnings.warn(
            "The output of 'find_outcomes' is paginated. Use 'find_outcomes_iter' instead.",
            DeprecationWarning
        )

        # we call this "find outcomes" for consistency with other methods, but it's not particularly useful for finding
        # specific outcomes yet due to the lack of filtering options
        return self._get(
            "/outcomes",
            params={
                "page": page,
                "completed": completed,
            },
        )

    find_outcomes_iter = make_iter_method("find_outcomes", "outcomes")
    find_outcomes_iter.__name__ = str("find_outcomes_iter")

    # Communications

    def find_communications(
        self,
        framework=None,
        supplier_id=None,
        latest_message_target=None,
        resolved=None,
        resolution=None,
        category=None,
        subject=None,
        supplier_name=None,
        message_text=None,
        sort_by=None,
        page=None,
    ):
        params = {
            'page': page,
            'framework': framework,
            'supplier_id': supplier_id,
            'latest_message_target': latest_message_target,
            'resolved': resolved,
            'resolution': resolution,
            'category': category,
            'subject': subject,
            'supplier_name': supplier_name,
            'message_text': message_text,
            'sort_by': sort_by,
        }

        return self._get("/communications", params=params)

    find_communications_iter = make_iter_method('find_communications', 'communications')
    find_communications_iter.__name__ = str("find_communications_iter")

    def get_communication(self, communication_id):
        return self._get(
            "/communications/{}".format(communication_id)
        )

    def update_communication(self, communication_id, communication, user=None):
        return self._post_with_updated_by(
            "/communications/{}".format(communication_id),
            data={
                "communications": communication,
            },
            user=user,
        )

    def resolve_communication(self, communication_id, resolved_by_user_id, resolution, user=None):
        return self._post_with_updated_by(
            "/communications/{}/resolve".format(communication_id),
            data={
                "resolvedByUserId": int(resolved_by_user_id),
                "resolution": resolution
            },
            user=user,
        )

    def undo_resolve_communication(self, communication_id, user=None):
        return self._post_with_updated_by(
            "/communications/{}/undo-resolve".format(communication_id),
            data={},
            user=user,
        )

    def read_communication_message(self, communication_message_id, read_by_user_id, user=None):
        return self._post_with_updated_by(
            "/communications/messages/{}/read".format(communication_message_id),
            data={"readByUserId": int(read_by_user_id)},
            user=user,
        )

    def create_communication_message(self, communication_id, message, attachments=None, user=None):
        if attachments is not None:
            message["attachments"] = attachments

        return self._post_with_updated_by(
            "/communications/{}/messages".format(communication_id),
            data={
                "communicationMessages": message,
            },
            user=user,
        )

    def create_communication(
        self,
        supplier_id,
        framework_slug,
        category,
        subject,
        message,
        attachments=None,
        user=None
    ):
        if attachments is not None:
            message["attachments"] = attachments

        return self._post_with_updated_by(
            "/communications",
            data={
                "communications": {
                    "supplierId": supplier_id,
                    "frameworkSlug": framework_slug,
                    "category": category,
                    "subject": subject,
                    "messages": message
                },
            },
            user=user,
        )

    def get_framework_communication_categories(self, framework_slug):
        return self._get(
            f'/communications/{framework_slug}/categories'
        )

    # System message

    def get_system_message(self, slug):
        return self._get(
            "/system-messages/{}".format(slug)
        )

    def create_system_message(
        self,
        slug,
        data,
        show=None,
        user=None
    ):
        system_message = {
            "slug": slug,
            "data": data,
        }

        if show is not None:
            system_message["show"] = show

        return self._post_with_updated_by(
            "/system-messages",
            data={
                "systemMessages": system_message,
            },
            user=user,
        )

    def update_system_message(
        self,
        slug,
        data=None,
        show=None,
        user=None
    ):
        system_message = {}

        if data is not None:
            system_message["data"] = data

        if show is not None:
            system_message["show"] = show

        return self._post_with_updated_by(
            "/system-messages/{}".format(slug),
            data={
                "systemMessages": system_message,
            },
            user=user,
        )

    # Lot Question Responses

    def find_lot_questions_responses(
        self,
        supplier_id,
        framework_slug,
        page=None,
    ):
        params = {
            'framework': framework_slug,
            'supplier_id': supplier_id,
            'page': page,
        }

        return self._get("/lot-questions-responses", params=params)

    find_lot_questions_responses_iter = make_iter_method('find_lot_questions_responses', 'lotQuestionsResponses')
    find_lot_questions_responses_iter.__name__ = str("find_lot_questions_responses_iter")

    def find_lot_questions_responses_by_framework_lot_route(
        self,
        framework_slug,
        route,
        page=None,
    ):
        params = {
            'framework': framework_slug,
            'route': route,
            'page': page,
        }

        return self._get("/lot-questions-responses", params=params)

    find_lot_questions_responses_by_framework_lot_route_iter = make_iter_method(
        'find_lot_questions_responses_by_framework_lot_route',
        'lotQuestionsResponses'
    )
    find_lot_questions_responses_by_framework_lot_route_iter.__name__ = str(
        "find_lot_questions_responses_by_framework_lot_route_iter"
    )

    def find_lot_questions_responses_applicants_for_framework_route(
        self,
        framework_slug,
        route,
        with_evaluations=None,
        page=None,
    ):
        params = {
            'framework': framework_slug,
            'route': route,
            'with_evaluations': with_evaluations,
            'page': page,
        }

        return self._get("/lot-questions-responses/applications", params=params)

    find_lot_questions_responses_applicants_for_framework_route_iter = \
        make_iter_method('find_lot_questions_responses_applicants_for_framework_route', 'lotQuestionsResponses')
    find_lot_questions_responses_applicants_for_framework_route_iter.__name__ = \
        str("find_lot_questions_responses_applicants_for_framework_route_iter")

    def create_lot_questions_response(self, supplier_id, framework_slug, route, user=None):
        return self._post_with_updated_by(
            "/lot-questions-responses",
            data={
                "supplierId": supplier_id,
                "frameworkSlug": framework_slug,
                "route": route,
            },
            user=user,
        )

    def get_lot_questions_response(self, lot_questions_response_id, with_evaluations=None):
        return self._get(
            f"/lot-questions-responses/{lot_questions_response_id}",
            params={
                "with_evaluations": with_evaluations
            }
        )

    def get_lot_questions_response_by_framework_route_suppler(self, framework_slug, route, supplier_id):
        return self._get(
            f"/lot-questions-responses/frameworks/{framework_slug}/routes/{route}/suppliers/{supplier_id}"
        )

    def update_lot_questions_response(
        self,
        lot_questions_response_id,
        lot_questions_response,
        user=None,
        page_questions=None
    ):
        data = {
            "lotQuestionsResponses": lot_questions_response,
        }

        if page_questions is not None:
            data['page_questions'] = page_questions

        return self._patch_with_updated_by(
            f"/lot-questions-responses/{lot_questions_response_id}",
            data=data,
            user=user,
        )

    def validate_lot_questions_response(
        self,
        lot_questions_response_id,
        lot_questions_response,
        page_questions=None
    ):
        data = {
            "lotQuestionsResponses": lot_questions_response,
        }

        if page_questions is not None:
            data['page_questions'] = page_questions

        return self._post(
            f"/lot-questions-responses/{lot_questions_response_id}/validate",
            data=data,
        )

    def complete_lot_questions_response(self, lot_questions_response_id, user=None):
        return self._post_with_updated_by(
            f"/lot-questions-responses/{lot_questions_response_id}/complete",
            data={},
            user=user,
        )

    def find_lot_questions_response_section_evaluations(
        self,
        framework,
        route,
        section_slug=None,
        page=None,
    ):
        params = {
            'framework': framework,
            'route': route,
            'section_slug': section_slug,
            'page': page
        }

        return self._get("/lot-questions-response-section-evaluations", params=params)

    find_lot_questions_response_section_evaluations_iter = make_iter_method(
        'find_lot_questions_response_section_evaluations',
        'lotQuestionsResponseSectionEvaluations'
    )
    find_lot_questions_response_section_evaluations_iter.__name__ = str(
        "find_lot_questions_response_section_evaluations_iter"
    )

    def get_lot_questions_response_section_evaluation(
        self,
        lot_questions_response_section_evaluation_id,
    ):
        return self._get(
            "/lot-questions-response-section-evaluations"
            f"/{lot_questions_response_section_evaluation_id}"
        )

    def create_lot_questions_response_section_evaluation(
        self,
        lot_questions_response_id,
        section_slug,
        lot_questions_response_section_evaluation,
        page_questions,
        user=None
    ):
        return self._post_with_updated_by(
            '/lot-questions-response-section-evaluations',
            data={
                'lotQuestionsResponseId': lot_questions_response_id,
                'sectionSlug': section_slug,
                'lotQuestionsResponseSectionEvaluations': lot_questions_response_section_evaluation,
                'page_questions': page_questions
            },
            user=user,
        )

    def update_lot_questions_response_section_evaluation(
        self,
        lot_questions_response_section_evaluation_id,
        lot_questions_response_section_evaluation,
        user=None
    ):
        return self._post_with_updated_by(
            '/lot-questions-response-section-evaluations'
            f'/{lot_questions_response_section_evaluation_id}',
            data={
                'lotQuestionsResponseSectionEvaluations': lot_questions_response_section_evaluation,
            },
            user=user,
        )

    # Evaluations

    def find_evaluator_framework_lots(
        self,
        framework=None,
        route=None,
        user_id=None,
        assigned=True,
        with_sections=None,
        with_evaluations=None,
        page=None,
    ):
        params = {
            'framework': framework,
            'route': route,
            'assigned': bool(assigned),
            'page': page,
            'user_id': user_id,
            'with_sections': with_sections,
            'with_evaluations': with_evaluations,
        }

        return self._get("/evaluations/evaluator-framework-lots", params=params)

    find_evaluator_framework_lots_iter = make_iter_method('find_evaluator_framework_lots', 'evaluatorFrameworkLots')
    find_evaluator_framework_lots_iter.__name__ = str("find_evaluator_framework_lots_iter")

    def update_assigned_evaluators_for_framework_lot(
        self,
        framework,
        route,
        users,
        user=None
    ):
        return self._post_with_updated_by(
            "/evaluations/evaluator-framework-lots",
            data={
                'evaluatorFrameworkLots': {
                    'frameworkSlug': framework,
                    "route": route,
                    'users': users,
                }
            },
            user=user,
        )

    def get_evaluator_framework_lot(
        self,
        evaluator_framework_lot_id,
        with_sections=True,
        with_evaluations=True,
    ):
        params = {
            'with_sections': bool(with_sections),
            'with_evaluations': bool(with_evaluations),
        }

        return self._get(f"/evaluations/evaluator-framework-lots/{evaluator_framework_lot_id}", params=params)

    def find_evaluator_framework_lot_sections(
        self,
        framework,
        route,
        assigned=True,
        section_slug=None,
        locked=None,
        with_evaluations=None,
        page=None,
    ):
        params = {
            'framework': framework,
            'route': route,
            'assigned': bool(assigned),
            'section_slug': section_slug,
            'locked': locked,
            'with_evaluations': with_evaluations,
            'page': page
        }

        return self._get("/evaluations/evaluator-framework-lot-sections", params=params)

    find_evaluator_framework_lot_sections_iter = make_iter_method(
        'find_evaluator_framework_lot_sections',
        'evaluatorFrameworkLotSections'
    )
    find_evaluator_framework_lot_sections_iter.__name__ = str("find_evaluator_framework_lot_sections_iter")

    def update_assigned_sections_for_evaluator_framework_lot(
        self,
        framework,
        route,
        section_slug,
        evaluator_framework_lots,
        user=None
    ):
        return self._post_with_updated_by(
            "/evaluations/evaluator-framework-lot-sections",
            data={
                'evaluatorFrameworkLotSections': {
                    'evaluatorFrameworkLots': evaluator_framework_lots,
                    'frameworkSlug': framework,
                    "route": route,
                    'sectionSlug': section_slug,
                }
            },
            user=user,
        )

    def get_evaluator_framework_lot_section(
        self,
        evaluator_framework_lot_section_id,
        with_evaluations=True,
    ):
        params = {
            'with_evaluations': bool(with_evaluations),
        }

        return self._get(
            "/evaluations/evaluator-framework-lot-sections/"
            f"{evaluator_framework_lot_section_id}",
            params=params
        )

    def update_evaluator_framework_lot_section_status(
        self,
        evaluator_framework_lot_section_id,
        status,
        user=None
    ):
        return self._post_with_updated_by(
            f"/evaluations/evaluator-framework-lot-sections/{evaluator_framework_lot_section_id}/status/{status}",
            data={},
            user=user,
        )

    def find_evaluator_framework_lot_section_evaluations(
        self,
        framework,
        route,
        section_slug=None,
        evaluator_framework_lot_id=None,
        supplier_id=None,
        page=None,
    ):
        params = {
            'framework': framework,
            'route': route,
            'section_slug': section_slug,
            'evaluator_framework_lot_id': evaluator_framework_lot_id,
            'supplier_id': supplier_id,
            'page': page
        }

        return self._get("/evaluations/evaluator-framework-lot-section-evaluations", params=params)

    find_evaluator_framework_lot_section_evaluations_iter = make_iter_method(
        'find_evaluator_framework_lot_section_evaluations',
        'evaluatorFrameworkLotSectionEvaluations'
    )
    find_evaluator_framework_lot_section_evaluations_iter.__name__ = str(
        "find_evaluator_framework_lot_section_evaluations_iter"
    )

    def create_evaluator_framework_lot_section_evaluation(
        self,
        evaluator_framework_lot_section_id,
        supplier_id,
        evaluator_framework_lot_section_evaluation,
        page_questions,
        user=None
    ):
        return self._post_with_updated_by(
            '/evaluations/evaluator-framework-lot-section-evaluations',
            data={
                'evaluatorFrameworkLotSectionId': evaluator_framework_lot_section_id,
                'supplierId': supplier_id,
                'evaluatorFrameworkLotSectionEvaluations': evaluator_framework_lot_section_evaluation,
                'page_questions': page_questions
            },
            user=user,
        )

    def get_evaluator_framework_lot_section_evaluation(
        self,
        evaluator_framework_lot_section_evaluation_id,
        with_lot_questions_response=None
    ):
        return self._get(
            "/evaluations/evaluator-framework-lot-section-evaluations/"
            f"{evaluator_framework_lot_section_evaluation_id}",
            params={
                "with_lot_questions_response": with_lot_questions_response
            }
        )

    def update_evaluator_framework_lot_section_evaluation(
        self,
        evaluator_framework_lot_section_evaluation_id,
        evaluator_framework_lot_section_evaluation,
        user=None
    ):
        return self._post_with_updated_by(
            '/evaluations/evaluator-framework-lot-section-evaluations'
            f'/{evaluator_framework_lot_section_evaluation_id}',
            data={
                'evaluatorFrameworkLotSectionEvaluations': evaluator_framework_lot_section_evaluation,
            },
            user=user,
        )

    # Technical award questions

    def find_technical_ability_certificates(
        self,
        supplier_id,
        framework_slug,
        page=None,
    ):
        params = {
            'framework': framework_slug,
            'supplier_id': supplier_id,
            'page': page,
        }

        return self._get("/technical-ability-certificates", params=params)

    find_technical_ability_certificates_iter = make_iter_method(
        'find_technical_ability_certificates',
        'technicalAbilityCertificates'
    )
    find_technical_ability_certificates_iter.__name__ = str("find_technical_ability_certificates_iter")

    def create_technical_ability_certificate(self, supplier_id, framework_slug, route, user=None):
        return self._post_with_updated_by(
            "/technical-ability-certificates",
            data={
                "supplierId": supplier_id,
                "frameworkSlug": framework_slug,
                "route": route,
            },
            user=user,
        )

    def get_technical_ability_certificate(self, technical_ability_certificate_id):
        return self._get(f"/technical-ability-certificates/{technical_ability_certificate_id}")

    def authenticate_technical_ability_certificate(
        self,
        authentication_id,
        passcode,
        user=None,
    ):
        return self._post_with_updated_by(
            "/technical-ability-certificates/auth",
            data={
                'authTechnicalAbilityCertificates': {
                    'authenticationId': authentication_id,
                    'passcode': passcode,
                }
            },
            user=user,
        )

    def verify_technical_ability_certificate_can_be_signed(
        self,
        authentication_id,
    ):
        return self._post(
            "/technical-ability-certificates/verify-can-be-signed",
            data={
                'verifyTechnicalAbilityCertificates': {
                    'authenticationId': authentication_id,
                }
            }
        )

    def update_technical_ability_certificate(
        self,
        technical_ability_certificate_id,
        technical_ability_certificate,
        user=None,
        page_questions=None
    ):
        data = {
            "technicalAbilityCertificates": technical_ability_certificate,
        }

        if page_questions is not None:
            data['page_questions'] = page_questions

        return self._patch_with_updated_by(
            f"/technical-ability-certificates/{technical_ability_certificate_id}",
            data=data,
            user=user,
        )

    def send_technical_ability_certificate(
        self,
        technical_ability_certificate_id,
        user=None,
    ):
        return self._post_with_updated_by(
            f"/technical-ability-certificates/{technical_ability_certificate_id}/send",
            data={},
            user=user,
        )

    def revert_technical_ability_certificate_to_in_progress(
        self,
        technical_ability_certificate_id,
        user=None,
    ):
        return self._post_with_updated_by(
            f"/technical-ability-certificates/{technical_ability_certificate_id}/revert-to-in-progress",
            data={},
            user=user,
        )

    def approve_technical_ability_certificate(
        self,
        technical_ability_certificate_id,
        electronic_signature,
        user=None,
    ):
        return self._post_with_updated_by(
            f"/technical-ability-certificates/{technical_ability_certificate_id}/approve",
            data={
                'electronicSignature': electronic_signature
            },
            user=user,
        )

    # Lot pricing

    def find_lot_pricings(
        self,
        supplier_id,
        framework_slug,
        page=None,
    ):
        params = {
            'framework': framework_slug,
            'supplier_id': supplier_id,
            'page': page,
        }

        return self._get("/lot-pricings", params=params)

    find_lot_pricings_iter = make_iter_method(
        'find_lot_pricings',
        'lotPricings'
    )
    find_lot_pricings_iter.__name__ = str("find_lot_pricings_iter")

    def find_lot_pricings_by_framework_lot_route(
        self,
        framework_slug,
        route,
        page=None,
    ):
        params = {
            'framework': framework_slug,
            'route': route,
            'page': page,
        }

        return self._get("/lot-pricings", params=params)

    find_lot_pricings_by_framework_lot_route_iter = make_iter_method(
        'find_lot_pricings_by_framework_lot_route',
        'lotPricings'
    )
    find_lot_pricings_by_framework_lot_route_iter.__name__ = str("find_lot_pricings_by_framework_lot_route_iter")

    def create_lot_pricing(self, supplier_id, framework_slug, route, user=None):
        return self._post_with_updated_by(
            "/lot-pricings",
            data={
                "supplierId": supplier_id,
                "frameworkSlug": framework_slug,
                "route": route,
            },
            user=user,
        )

    def get_lot_pricing(self, lot_pricing_id):
        return self._get(f"/lot-pricings/{lot_pricing_id}")

    def update_lot_pricing(
        self,
        lot_pricing_id,
        lot_pricing,
        user=None,
        page_questions=None
    ):
        data = {
            "lotPricings": lot_pricing,
        }

        if page_questions is not None:
            data['page_questions'] = page_questions

        return self._patch_with_updated_by(
            f"/lot-pricings/{lot_pricing_id}",
            data=data,
            user=user,
        )

    def complete_lot_pricing(
        self,
        lot_pricing_id,
        user=None,
    ):
        return self._post_with_updated_by(
            f"/lot-pricings/{lot_pricing_id}/complete",
            data={},
            user=user,
        )
