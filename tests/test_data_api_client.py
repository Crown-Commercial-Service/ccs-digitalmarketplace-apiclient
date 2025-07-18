# -*- coding: utf-8 -*-
from flask import json
import pytest
from unittest import mock

from dmapiclient import DataAPIClient
from dmapiclient import APIError, HTTPError
from dmapiclient.audit import AuditTypes


@pytest.fixture
def data_client():
    return DataAPIClient('http://baseurl', 'auth-token', True)


class TestDataApiClient(object):
    def test_init_app_sets_attributes(self, data_client):
        app = mock.Mock()
        app.config = {
            "DM_DATA_API_URL": "http://example",
            "DM_DATA_API_AUTH_TOKEN": "example-token",
        }
        data_client.init_app(app)

        assert data_client.base_url == "http://example"
        assert data_client.auth_token == "example-token"

    def test_get_status(self, data_client, rmock):
        rmock.get(
            "http://baseurl/_status",
            json={"status": "ok"},
            status_code=200)

        result = data_client.get_status()

        assert result['status'] == "ok"
        assert rmock.called

    def test_updated_by_user_can_be_set_in_constructor(self, rmock):
        data_client = DataAPIClient('http://baseurl', 'auth-token', user="testuser@example.com", enabled=True)

        rmock.patch(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7/declaration",
            json={"declaration": {"question": "answer"}},
            status_code=200)

        data_client.update_supplier_declaration(123, 'g-cloud-7', {"question": "answer"})

        assert rmock.request_history[0].json() == {
            'updated_by': 'testuser@example.com',
            'declaration': {'question': 'answer'}}

    def test_value_error_is_raised_if_no_user_in_constructor_or_method_call(self, data_client, rmock):
        rmock.patch(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7/declaration",
            json={"declaration": {"question": "answer"}},
            status_code=200)

        with pytest.raises(ValueError):
            data_client.update_supplier_declaration(123, 'g-cloud-7', {"question": "answer"})


class TestServiceMethods(object):
    def test_get_archived_service(self, data_client, rmock):
        rmock.get(
            "http://baseurl/archived-services/123",
            json={"services": "result"},
            status_code=200)

        result = data_client.get_archived_service(123)

        assert result == {"services": "result"}
        assert rmock.called

    def test_get_service(self, data_client, rmock):
        rmock.get(
            "http://baseurl/services/123",
            json={"services": "result"},
            status_code=200)

        result = data_client.get_service(123)

        assert result == {"services": "result"}
        assert rmock.called

    def test_get_service_returns_none_on_404(self, data_client, rmock):
        rmock.get(
            'http://baseurl/services/123',
            json={'services': 'result'},
            status_code=404)

        result = data_client.get_service(123)

        assert result is None

    def test_get_service_raises_on_non_404(self, data_client, rmock):
        with pytest.raises(APIError):
            rmock.get(
                'http://baseurl/services/123',
                json={'services': 'result'},
                status_code=400)

            data_client.get_service(123)

    def test_find_services(self, data_client, rmock):
        rmock.get(
            "http://baseurl/services",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_services()

        assert result == {"services": "result"}
        assert rmock.called

    def test_find_services_adds_page_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/services?page=2",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_services(page=2)

        assert result == {"services": "result"}
        assert rmock.called

    def test_find_services_adds_supplier_id_parameter(
            self, data_client, rmock):
        rmock.get(
            "http://baseurl/services?supplier_id=1",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_services(supplier_id=1)

        assert result == {"services": "result"}
        assert rmock.called

    def test_update_service(self, data_client, rmock):
        rmock.post(
            "http://baseurl/services/123?&wait-for-index=true",
            json={"services": "result"},
            status_code=200,
        )

        result = data_client.update_service(
            123, {"foo": "bar"}, "person")

        assert result == {"services": "result"}
        assert rmock.called

    @pytest.mark.parametrize("wait_for_index_call_arg,wait_for_index_req_arg", (
        (False, "false"),
        (True, "true"),
    ))
    def test_update_service_by_admin(self, data_client, rmock, wait_for_index_call_arg, wait_for_index_req_arg):
        rmock.post(
            f"http://baseurl/services/123?&wait-for-index={wait_for_index_req_arg}&user-role=admin",
            json={"services": "result"},
            status_code=200,
        )

        result = data_client.update_service(
            123, {"foo": "bar"}, "person", user_role='admin', wait_for_index=wait_for_index_call_arg)

        assert result == {"services": "result"}
        assert rmock.called

    @pytest.mark.parametrize("wait_for_index_call_arg,wait_for_index_req_arg", (
        (False, "false"),
        (True, "true"),
    ))
    def test_update_service_status(self, data_client, rmock, wait_for_index_call_arg, wait_for_index_req_arg):
        rmock.post(
            f"http://baseurl/services/123/status/published?wait-for-index={wait_for_index_req_arg}",
            json={"services": "result"},
            status_code=200,
        )

        result = data_client.update_service_status(
            123, "published", "person", wait_for_index=wait_for_index_call_arg)

        assert result == {"services": "result"}
        assert rmock.called

    def test_revert_service(self, data_client, rmock):
        rmock.post(
            "http://baseurl/services/123/revert",
            json={},
            status_code=200,
        )

        data_client.revert_service(123, 314159, "jollypoldy@example.com")

        assert tuple(req.json() for req in rmock.request_history) == (
            {
                "archivedServiceId": 314159,
                "updated_by": "jollypoldy@example.com",
            },
        )


class TestUserMethods(object):
    @staticmethod
    def user():
        return {'users': {
            'id': 'id',
            'email_address': 'email_address',
            'name': 'name',
            'role': 'supplier',
            'active': True,
            'locked': False,
            'created_at': "2015-05-05T05:05:05",
            'updated_at': "2015-05-05T05:05:05",
            'password_changed_at': "2015-05-05T05:05:05",
            'personal_data_removed': False,
            'user_research_opted_in': False,
            'supplier': {
                'supplier_id': 1234,
                'name': 'name'
            },
        }}

    def test_find_users_by_supplier_id(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users?supplier_id=1234",
            json=self.user(),
            status_code=200)
        user = data_client.find_users(1234)

        assert user == self.user()

    def test_find_users_not_possible_with_supplier_id_and_role(self, data_client, rmock):
        with pytest.raises(ValueError):
            data_client.find_users(supplier_id=123, role='buyer')

    def test_find_users_by_role(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users?role=buyer",
            json=self.user(),
            status_code=200)

        user = data_client.find_users(role='buyer')

        assert user == self.user()

    def test_find_users_by_page(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users?page=12",
            json=self.user(),
            status_code=200)
        user = data_client.find_users(page=12)

        assert user == self.user()

    def test_find_users_by_personal_data_removed_false(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users?personal_data_removed=false",
            json=self.user(),
            status_code=200)
        user = data_client.find_users(personal_data_removed=False)

        assert user == self.user()

    def test_find_users_by_personal_data_removed_true(self, data_client, rmock):
        user = self.user()
        user['users'].update({'personal_data_removed': True})
        expected_data = user.copy()

        rmock.get(
            "http://baseurl/users?personal_data_removed=true",
            json=user,
            status_code=200)
        user = data_client.find_users(personal_data_removed=True)

        assert user == expected_data

    def test_find_users_by_user_research_opted_in_false(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users?user_research_opted_in=false",
            json=self.user(),
            status_code=200)
        user = data_client.find_users(user_research_opted_in=False)

        assert user == self.user()

    def test_find_users_by_user_research_opted_in_true(self, data_client, rmock):
        user = self.user()
        user['users'].update({'user_research_opted_in': True})
        expected_data = user.copy()

        rmock.get(
            "http://baseurl/users?user_research_opted_in=true",
            json=user,
            status_code=200)
        user = data_client.find_users(user_research_opted_in=True)

        assert user == expected_data

    def test_find_users_by_active_false(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users?active=false",
            json=self.user(),
            status_code=200)
        user = data_client.find_users(active=False)

        assert user == self.user()

    def test_find_users_by_active_true(self, data_client, rmock):
        user = self.user()
        user['users'].update({'active': True})
        expected_data = user.copy()

        rmock.get(
            "http://baseurl/users?active=true",
            json=user,
            status_code=200)
        user = data_client.find_users(active=True)

        assert user == expected_data

    def test_get_user_by_id(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users/1234",
            json=self.user(),
            status_code=200)
        user = data_client.get_user(user_id=1234)

        assert user == self.user()

    def test_get_user_by_email_address(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users?email_address=myemail",
            json=self.user(),
            status_code=200)
        user = data_client.get_user(email_address="myemail")

        assert user == self.user()

    def test_get_user_fails_if_both_email_and_id_are_provided(
            self, data_client, rmock):

        with pytest.raises(ValueError):
            data_client.get_user(user_id=123, email_address="myemail")

    def test_get_user_fails_if_neither_email_or_id_are_provided(
            self, data_client, rmock):

        with pytest.raises(ValueError):
            data_client.get_user()

    def test_get_user_returns_none_on_404(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users/123",
            json={"not": "found"},
            status_code=404)

        user = data_client.get_user(user_id=123)

        assert user is None

    def test_authenticate_user_is_called_with_correct_params(
            self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/auth",
            json=self.user(),
            status_code=200)

        user = data_client.authenticate_user("email_address", "password")['users']

        assert user['id'] == "id"
        assert user['email_address'] == "email_address"
        assert user['supplier']['supplier_id'] == 1234
        assert user['supplier']['name'] == "name"

    def test_authenticate_user_returns_none_on_404(
            self, data_client, rmock):
        rmock.post(
            'http://baseurl/users/auth',
            text=json.dumps({'authorization': False}),
            status_code=404)

        user = data_client.authenticate_user("email_address", "password")

        assert user is None

    def test_authenticate_user_returns_none_on_403(
            self, data_client, rmock):
        rmock.post(
            'http://baseurl/users/auth',
            text=json.dumps({'authorization': False}),
            status_code=403)

        user = data_client.authenticate_user("email_address", "password")

        assert user is None

    def test_authenticate_user_returns_none_on_400(
            self, data_client, rmock):
        rmock.post(
            'http://baseurl/users/auth',
            text=json.dumps({'authorization': False}),
            status_code=400)

        user = data_client.authenticate_user("email_address", "password")

        assert user is None

    def test_authenticate_user_returns_buyer_user(
            self, data_client, rmock):
        user_with_no_supplier = self.user()
        del user_with_no_supplier['users']['supplier']
        user_with_no_supplier['users']['role'] = 'buyer'

        rmock.post(
            'http://baseurl/users/auth',
            text=json.dumps(user_with_no_supplier),
            status_code=200)

        user = data_client.authenticate_user("email_address", "password")

        assert user == user_with_no_supplier

    def test_authenticate_user_raises_on_500(self, data_client, rmock):
        with pytest.raises(APIError):
            rmock.post(
                'http://baseurl/users/auth',
                text=json.dumps({'authorization': False}),
                status_code=500)

            data_client.authenticate_user("email_address", "password")

    def test_create_user(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users",
            json={"users": "result"},
            status_code=201)

        result = data_client.create_user({"foo": "bar"})

        assert result == {"users": "result"}
        assert rmock.called

    def test_update_user_password(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/123",
            json={},
            status_code=200)
        assert data_client.update_user_password(123, "newpassword")
        assert rmock.last_request.json() == {
            "users": {
                "password": "newpassword"
            },
            "updated_by": "no logged-in user"
        }

    def test_update_user_password_by_logged_in_user(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/123",
            json={},
            status_code=200)
        assert data_client.update_user_password(123, "newpassword", "test@example.com")
        assert rmock.last_request.json() == {
            "users": {
                "password": "newpassword"
            },
            "updated_by": "test@example.com"
        }

    def test_update_user_password_with_user_property(self, rmock):
        data_client = DataAPIClient('http://baseurl', 'auth-token', user="testuser@example.com", enabled=True)
        rmock.post(
            "http://baseurl/users/123",
            json={},
            status_code=200)
        assert data_client.update_user_password(123, "newpassword")
        assert rmock.last_request.json() == {
            "users": {
                "password": "newpassword"
            },
            "updated_by": "testuser@example.com"
        }

    def test_update_user_password_returns_false_on_non_200(
            self, data_client, rmock):
        for status_code in [400, 403, 404, 500]:
            rmock.post(
                "http://baseurl/users/123",
                json={},
                status_code=status_code)
            assert not data_client.update_user_password(123, "newpassword")

    def test_update_user_returns_false_on_non_200(self, data_client, rmock):
        for status_code in [400, 403, 404, 500]:
            rmock.post(
                "http://baseurl/users/123",
                json={},
                status_code=status_code)
            with pytest.raises(HTTPError) as e:
                data_client.update_user(123)

            assert e.value.status_code == status_code

    def test_can_change_user_role(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/123",
            json={},
            status_code=200)
        data_client.update_user(123, role='supplier', updater="test@example.com")
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "users": {"role": 'supplier'}
        }

    def test_can_add_user_supplier_id(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/123",
            json={},
            status_code=200)
        data_client.update_user(123, supplier_id=123, updater="test@example.com")
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "users": {"supplierId": 123}
        }

    def test_make_user_a_supplier(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/123",
            json={},
            status_code=200)
        data_client.update_user(123, supplier_id=123, role='supplier', updater="test@example.com")
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "users": {
                "supplierId": 123,
                "role": "supplier"
            }
        }

    def test_can_unlock_user(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/123",
            json={},
            status_code=200)
        data_client.update_user(123, locked=False, updater="test@example.com")
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "users": {"locked": False}
        }

    def test_can_activate_user(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/123",
            json={},
            status_code=200)
        data_client.update_user(123, active=True, updater="test@example.com")
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "users": {"active": True}
        }

    def test_can_deactivate_user(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/123",
            json={},
            status_code=200)
        data_client.update_user(123, active=False, updater="test@example.com")
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "users": {"active": False}
        }

    def test_can_update_user_name(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/123",
            json={},
            status_code=200)
        data_client.update_user(123, name="Star Butterfly", updater="test@example.com")
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "users": {"name": "Star Butterfly"}
        }

    def test_can_remove_user_personal_data(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/123/remove-personal-data",
            json={},
            status_code=200
        )
        data_client.remove_user_personal_data(123, "test@example.com")
        assert rmock.called
        assert rmock.last_request.json() == {"updated_by": "test@example.com"}

    def test_can_export_users(self, data_client, rmock):
        rmock.get(
            "http://baseurl/users/export/g-cloud-7",
            json={"users": "result"},
            status_code=200)
        result = data_client.export_users('g-cloud-7')
        assert rmock.called
        assert result == {"users": "result"}

    def test_can_update_user_research_opted_ins(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/123",
            json={},
            status_code=200)
        data_client.update_user(123, user_research_opted_in=True, updater="test@example.com")
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "users": {"userResearchOptedIn": True}
        }


class TestBuyerDomainMethods(object):
    def test_is_email_address_with_valid_buyer_domain_true(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/check-buyer-email",
            json={"valid": True},
            status_code=200)
        result = data_client.is_email_address_with_valid_buyer_domain('kev@gov.uk')
        assert rmock.called
        assert rmock.last_request.json() == {'emailAddress': 'kev@gov.uk'}
        assert result is True

    def test_is_email_address_with_valid_buyer_domain_false(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/check-buyer-email",
            json={"valid": False},
            status_code=200)
        result = data_client.is_email_address_with_valid_buyer_domain('kev@ymail.com')
        assert rmock.called
        assert rmock.last_request.json() == {'emailAddress': 'kev@ymail.com'}
        assert result is False

    def test_get_buyer_email_domains(self, data_client, rmock):
        expected = {"buyerEmailDomains": [{"domainName": "gov.uk", "id": "1"}]}
        rmock.get(
            "http://baseurl/buyer-email-domains",
            json=expected,
            status_code=200,
        )

        got = data_client.get_buyer_email_domains()
        assert expected == got

    def test_get_buyer_email_domains_can_have_page(self, data_client, rmock):
        rmock.get(
            "http://baseurl/buyer-email-domains?page=2",
            json={},
            status_code=200,
        )

        data_client.get_buyer_email_domains(page=2)
        assert rmock.called

    def test_create_buyer_email_domain(self, data_client, rmock):
        rmock.post(
            "http://baseurl/buyer-email-domains",
            json={"buyerEmailDomains": "result"},
            status_code=201,
        )

        result = data_client.create_buyer_email_domain(
            "whatever.org", "user@email.com"
        )

        assert result == {"buyerEmailDomains": "result"}
        assert rmock.last_request.json() == {
            "buyerEmailDomains": {"domainName": "whatever.org"},
            "updated_by": "user@email.com"
        }

    def test_delete_buyer_email_domain(self, data_client, rmock):
        rmock.delete(
            "http://baseurl/buyer-email-domains",
            json={"buyerEmailDomains": "result"},
            status_code=201,
        )

        result = data_client.delete_buyer_email_domain(
            "whatever.org", "user@email.com"
        )

        assert result == {"buyerEmailDomains": "result"}
        assert rmock.last_request.json() == {
            "buyerEmailDomains": {"domainName": "whatever.org"},
            "updated_by": "user@email.com"
        }


class TestEmailValidForAdminMethod(object):

    def test_email_address_with_valid_admin_domain_is_true(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/valid-admin-email",
            json={"valid": True},
            status_code=200
        )
        result = data_client.email_is_valid_for_admin_user('kev@gov.uk')
        assert rmock.last_request.json() == {"emailAddress": "kev@gov.uk"}
        assert rmock.called
        assert result is True

    def test_email_address_with_invalid_admin_domain_is_false(self, data_client, rmock):
        rmock.post(
            "http://baseurl/users/valid-admin-email",
            json={"valid": False},
            status_code=200
        )
        result = data_client.email_is_valid_for_admin_user('kev@not-gov.uk')
        assert rmock.last_request.json() == {"emailAddress": "kev@not-gov.uk"}
        assert rmock.called
        assert result is False


class TestSupplierMethods(object):
    def test_find_suppliers_with_no_prefix(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_suppliers()

        assert result == {"services": "result"}
        assert rmock.called

    def test_find_suppliers_with_prefix(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers?prefix=a",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_suppliers(prefix='a')

        assert result == {"services": "result"}
        assert rmock.called

    def test_find_suppliers_with_name(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers?name=a",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_suppliers(name='a')

        assert result == {"services": "result"}
        assert rmock.called

    def test_find_suppliers_with_framework(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers?framework=gcloud",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_suppliers(framework='gcloud')

        assert result == {"services": "result"}
        assert rmock.called

    def test_find_suppliers_with_duns_number(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers?duns_number=1234",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_suppliers(duns_number='1234')

        assert result == {"services": "result"}
        assert rmock.called

    def test_find_suppliers_with_company_registration_number(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers?company_registration_number=12345678",
            json={"suppliers": "result"},
            status_code=200)

        result = data_client.find_suppliers(company_registration_number='12345678')

        assert result == {"suppliers": "result"}
        assert rmock.called

    def test_find_supplier_adds_page_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers?page=2",
            json={"suppliers": "result"},
            status_code=200)

        result = data_client.find_suppliers(page=2)

        assert result == {"suppliers": "result"}
        assert rmock.called

    def test_find_services_by_supplier(self, data_client, rmock):
        rmock.get(
            "http://baseurl/services?supplier_id=123",
            json={"services": "result"},
            status_code=200)

        result = data_client.find_services(supplier_id=123)

        assert result == {"services": "result"}
        assert rmock.called

    def test_get_supplier_by_id(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123",
            json={"services": "result"},
            status_code=200)

        result = data_client.get_supplier(123)

        assert result == {"services": "result"}
        assert rmock.called

    def test_get_supplier_by_id_should_return_404(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123",
            status_code=404)

        try:
            data_client.get_supplier(123)
        except HTTPError:
            assert rmock.called

    def test_get_supplier_with_cdp_supplier_information(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123?with_cdp_supplier_information=true",
            json={"services": "result"},
            status_code=200)

        result = data_client.get_supplier(123, with_cdp_supplier_information=True)

        assert result == {"services": "result"}
        assert rmock.called

    def test_create_supplier(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers",
            json={"suppliers": "result"},
            status_code=201,
        )

        result = data_client.create_supplier({"foo": "bar"})

        assert result == {"suppliers": "result"}
        assert rmock.called

    def test_update_supplier(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123",
            json={"suppliers": "result"},
            status_code=201,
        )

        result = data_client.update_supplier(123, {"foo": "bar"}, 'supplier')

        assert result == {"suppliers": "result"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'suppliers': {'foo': 'bar'}, 'updated_by': 'supplier'
        }

    def test_update_contact_information(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123/contact-information/2",
            json={"suppliers": "result"},
            status_code=201,
        )

        result = data_client.update_contact_information(
            123, 2, {"foo": "bar"}, 'supplier'
        )

        assert result == {"suppliers": "result"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'contactInformation': {'foo': 'bar'}, 'updated_by': 'supplier'
        }

    def test_remove_contact_information_personal_data(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123/contact-information/1/remove-personal-data",
            json={},
            status_code=200
        )
        data_client.remove_contact_information_personal_data(123, 1, "test@example.com")
        assert rmock.called
        assert rmock.last_request.json() == {"updated_by": "test@example.com"}

    def test_create_central_digital_platform_connection(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/1234/central-digital-platform/create",
            json={"message": "done"},
            status_code=200
        )

        result = data_client.create_central_digital_platform_connection(
            1234,
            {
                "supplierInformation": "value"
            },
            'My trading name',
            'user'
        )

        assert result == {'message': 'done'}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'centralDigitalPlatformData': {
                "supplierInformation": "value"
            },
            'tradingName': 'My trading name',
            'updated_by': 'user',
        }

    def test_revoke_central_digital_platform_connection(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/1234/central-digital-platform/revoke",
            json={"message": "done"},
            status_code=200
        )

        result = data_client.revoke_central_digital_platform_connection(
            1234,
            'user'
        )

        assert result == {'message': 'done'}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
        }

    def test_update_supplier_central_digital_platform_data(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/1234/central-digital-platform/update",
            json={"message": "done"},
            status_code=200
        )

        result = data_client.update_supplier_central_digital_platform_data(
            1234,
            {
                "supplierInformation": "value"
            },
            user='user'
        )

        assert result == {'message': 'done'}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'centralDigitalPlatformData': {
                "supplierInformation": "value"
            },
            'updated_by': 'user',
        }

    def test_update_supplier_central_digital_platform_data_frameworks_to_update(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/1234/central-digital-platform/update",
            json={"message": "done"},
            status_code=200
        )

        result = data_client.update_supplier_central_digital_platform_data(
            1234,
            {
                "supplierInformation": "value"
            },
            [
                'g-cloud-99',
                'dos-67',
            ],
            user='user'
        )

        assert result == {'message': 'done'}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'centralDigitalPlatformData': {
                "supplierInformation": "value"
            },
            'frameworksToUpdate': [
                'g-cloud-99',
                'dos-67',
            ],
            'updated_by': 'user',
        }

    def test_update_supplier_framework_central_digital_platform_data(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/1234/frameworks/g-things-99/central-digital-platform/update",
            json={"message": "done"},
            status_code=200
        )

        result = data_client.update_supplier_framework_central_digital_platform_data(
            1234,
            'g-things-99',
            {
                "supplierInformation": "value"
            },
            user='user'
        )

        assert result == {'message': 'done'}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'centralDigitalPlatformData': {
                "supplierInformation": "value"
            },
            'updated_by': 'user',
        }

    def test_verify_central_digital_platform_organisation(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/central-digital-platform/verify-organisation/123456",
            json={"message": "supplier-found"},
            status_code=200
        )

        result = data_client.verify_central_digital_platform_organisation(123456)

        assert result == {"message": "supplier-found"}
        assert rmock.called

    def test_get_framework_interest(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123/frameworks/interest",
            json={"frameworks": ['g-cloud-15', 'dos-23']},
            status_code=200)

        result = data_client.get_framework_interest(123)

        assert result == {"frameworks": ['g-cloud-15', 'dos-23']}
        assert rmock.called

    def test_register_framework_interest(self, data_client, rmock):
        rmock.put(
            "http://baseurl/suppliers/123/frameworks/g-cloud-15",
            json={"frameworkInterest": {"supplierId": 123, "frameworkId": 19}},
            status_code=200)

        result = data_client.register_framework_interest(123, 'g-cloud-15', "g-15-user")

        assert result == {"frameworkInterest": {"supplierId": 123, "frameworkId": 19}}
        assert rmock.called
        assert rmock.request_history[0].json() == {'updated_by': 'g-15-user'}

    def test_get_supplier_declaration(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7",
            json={"frameworkInterest": {"declaration": {"question": "answer"}}},
            status_code=200)

        result = data_client.get_supplier_declaration(123, 'g-cloud-7')

        assert result == {'declaration': {'question': 'answer'}}
        assert rmock.called

    def test_set_supplier_declaration(self, data_client, rmock):
        rmock.put(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7/declaration",
            json={"declaration": {"question": "answer"}},
            status_code=200)

        result = data_client.set_supplier_declaration(123, 'g-cloud-7', {"question": "answer"}, "user")

        assert result == {'declaration': {'question': 'answer'}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
            'declaration': {'question': 'answer'}}

    def test_update_supplier_declaration(self, data_client, rmock):
        rmock.patch(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7/declaration",
            json={"declaration": {"question": "answer"}},
            status_code=200)

        result = data_client.update_supplier_declaration(123, 'g-cloud-7', {"question": "answer"}, "user")

        assert result == {'declaration': {'question': 'answer'}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
            'declaration': {'question': 'answer'}}

    def test_remove_supplier_declaration(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7/declaration",
            json={"supplierFramework": "serialized_object"},
            status_code=200
        )

        result = data_client.remove_supplier_declaration(123, 'g-cloud-7', "user")

        assert result == {"supplierFramework": "serialized_object"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': "user"
        }

    def test_get_supplier_fvra(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7",
            json={"frameworkInterest": {"fvra": {"question": "answer"}}},
            status_code=200
        )

        result = data_client.get_supplier_fvra(123, 'g-cloud-7')

        assert result == {'fvra': {'question': 'answer'}}
        assert rmock.called

    def test_set_supplier_fvra_result(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7/set-fvra-result",
            json={"fvra": {"status": "in_progress"}},
            status_code=200
        )

        result = data_client.set_supplier_fvra_result(
            123,
            'g-cloud-7',
            'fvra_default',
            {
                'key': 'value'
            },
            {
                'CheckDate': '2025-03-20T04:00:00',
                'DUNS': '123456789',
                'FVRAStatus': 'Pass'
            },
            'user'
        )

        assert result == {'fvra': {'status': 'in_progress'}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
            "fvraFrozenResult": {
                'fvraRoute': 'fvra_default',
                'fvraAdditionalDeclarationAnswers': {
                    'key': 'value'
                },
                'fvraResults': {
                    'CheckDate': '2025-03-20T04:00:00',
                    'DUNS': '123456789',
                    'FVRAStatus': 'Pass'
                },
            }
        }

    def test_update_supplier_fvra(self, data_client, rmock):
        rmock.patch(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7/fvra",
            json={"fvra": {"question": "answer"}},
            status_code=200
        )

        result = data_client.update_supplier_fvra(123, 'g-cloud-7', {"question": "answer"}, "user")

        assert result == {'fvra': {'question': 'answer'}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
            'fvra': {'question': 'answer'}
        }

    def test_get_supplier_frameworks(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123/frameworks",
            json={"frameworkInterest": [{"declaration": {"status": "started"}}]},
            status_code=200)

        result = data_client.get_supplier_frameworks(123)

        assert result == {"frameworkInterest": [{"declaration": {"status": "started"}}]}
        assert rmock.called

    def test_get_supplier_frameworks_with_technical_ability_certificates(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123/frameworks?with_technical_ability_certificates=True",
            json={"frameworkInterest": [{"declaration": {"status": "started"}}]},
            status_code=200)
        result = data_client.get_supplier_frameworks(123, with_technical_ability_certificates=True)
        assert result == {"frameworkInterest": [{"declaration": {"status": "started"}}]}
        assert rmock.called

    def test_get_supplier_frameworks_with_lot_questions_responses(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123/frameworks?with_lot_questions_responses=True",
            json={"frameworkInterest": [{"declaration": {"status": "started"}}]},
            status_code=200)
        result = data_client.get_supplier_frameworks(123, with_lot_questions_responses=True)
        assert result == {"frameworkInterest": [{"declaration": {"status": "started"}}]}
        assert rmock.called

    def test_get_supplier_frameworks_with_lot_pricings(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123/frameworks?with_lot_pricings=True",
            json={"frameworkInterest": [{"declaration": {"status": "started"}}]},
            status_code=200)
        result = data_client.get_supplier_frameworks(123, with_lot_pricings=True)
        assert result == {"frameworkInterest": [{"declaration": {"status": "started"}}]}
        assert rmock.called

    def test_get_supplier_framework_info(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7",
            json={"frameworkInterest": {"supplierId": 123, "frameworkId": 2, "onFramework": False}},
            status_code=200)
        result = data_client.get_supplier_framework_info(123, 'g-cloud-7')
        assert result == {"frameworkInterest": {"supplierId": 123, "frameworkId": 2, "onFramework": False}}
        assert rmock.called

    def test_get_supplier_framework_info_with_technical_ability_certificates(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7?with_technical_ability_certificates=True",
            json={"frameworkInterest": {"supplierId": 123, "frameworkId": 2, "onFramework": False}},
            status_code=200)
        result = data_client.get_supplier_framework_info(123, 'g-cloud-7', with_technical_ability_certificates=True)
        assert result == {"frameworkInterest": {"supplierId": 123, "frameworkId": 2, "onFramework": False}}
        assert rmock.called

    def test_get_supplier_framework_info_with_lot_questions_responses(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7?with_lot_questions_responses=True",
            json={"frameworkInterest": {"supplierId": 123, "frameworkId": 2, "onFramework": False}},
            status_code=200)
        result = data_client.get_supplier_framework_info(123, 'g-cloud-7', with_lot_questions_responses=True)
        assert result == {"frameworkInterest": {"supplierId": 123, "frameworkId": 2, "onFramework": False}}
        assert rmock.called

    def test_get_supplier_framework_info_with_lot_pricings(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7?with_lot_pricings=True",
            json={"frameworkInterest": {"supplierId": 123, "frameworkId": 2, "onFramework": False}},
            status_code=200)
        result = data_client.get_supplier_framework_info(123, 'g-cloud-7', with_lot_pricings=True)
        assert result == {"frameworkInterest": {"supplierId": 123, "frameworkId": 2, "onFramework": False}}
        assert rmock.called

    def test_get_supplier_framework_info_with_cdp(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7?with_cdp_supplier_information=True",
            json={"frameworkInterest": {"supplierId": 123, "frameworkId": 2, "onFramework": False}},
            status_code=200)
        result = data_client.get_supplier_framework_info(123, 'g-cloud-7', with_cdp_supplier_information=True)
        assert result == {"frameworkInterest": {"supplierId": 123, "frameworkId": 2, "onFramework": False}}
        assert rmock.called

    def test_set_framework_result(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7",
            json={"frameworkInterest": {"onFramework": True}},
            status_code=200)

        result = data_client.set_framework_result(123, 'g-cloud-7', True, "user")
        assert result == {"frameworkInterest": {"onFramework": True}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'frameworkInterest': {'onFramework': True},
            'updated_by': 'user'
        }

    def test_set_supplier_framework_allow_declaration_reuse(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7",
            json={"frameworkInterest": {"allowDeclarationReuse": True}},
            status_code=200)

        result = data_client.set_supplier_framework_allow_declaration_reuse(123, 'g-cloud-7', True, "user")
        assert result == {"frameworkInterest": {"allowDeclarationReuse": True}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'frameworkInterest': {'allowDeclarationReuse': True},
            'updated_by': 'user'
        }

    def test_set_supplier_framework_prefill_declaration(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/8765/frameworks/breeches",
            json={"frameworkInterest": {"prefillDeclarationFromFrameworkSlug": "pyjamas"}},
            status_code=200)

        result = data_client.set_supplier_framework_prefill_declaration(8765, "breeches", "pyjamas", "user")
        assert result == {"frameworkInterest": {"prefillDeclarationFromFrameworkSlug": "pyjamas"}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            "frameworkInterest": {"prefillDeclarationFromFrameworkSlug": "pyjamas"},
            "updated_by": 'user'
        }

    def test_set_supplier_framework_application_company_details_confirmed(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/8765/frameworks/g-cloud-10",
            json={"frameworkInterest": {"applicationCompanyDetailsConfirmed": True}},
            status_code=200)

        result = data_client.set_supplier_framework_application_company_details_confirmed(8765, 'g-cloud-10', True,
                                                                                          'user')
        assert result == {"frameworkInterest": {"applicationCompanyDetailsConfirmed": True}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            "frameworkInterest": {"applicationCompanyDetailsConfirmed": True},
            "updated_by": 'user'
        }

    def test_set_supplier_framework_agreement_version(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/8765/frameworks/g-cloud-10",
            json={"frameworkInterest": {"agreementVersion": 'aegis'}},
            status_code=200)

        result = data_client.set_supplier_framework_agreement_version(
            8765,
            'g-cloud-10',
            'aegis',
            'user'
        )
        assert result == {"frameworkInterest": {"agreementVersion": 'aegis'}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            "frameworkInterest": {"agreementVersion": 'aegis'},
            "updated_by": 'user'
        }

    def test_register_framework_agreement_returned_with_uploader_user_id(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123/frameworks/g-cloud-8",
            json={
                'frameworkInterest': {
                    'agreementReturned': True,
                    'agreementDetails': {'uploaderUserId': 10},
                },
            },
            status_code=200)

        result = data_client.register_framework_agreement_returned(
            123, 'g-cloud-8', "user", 10
        )
        assert result == {
            'frameworkInterest': {
                'agreementReturned': True,
                'agreementDetails': {'uploaderUserId': 10},
            },
        }
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'frameworkInterest': {
                'agreementReturned': True,
                'agreementDetails': {'uploaderUserId': 10},
            },
            'updated_by': 'user',
        }

    def test_register_framework_agreement_returned_without_uploader_user_id(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7",
            json={
                'frameworkInterest': {
                    'agreementReturned': True,
                },
            },
            status_code=200)

        result = data_client.register_framework_agreement_returned(123, 'g-cloud-7', "user")
        assert result == {
            'frameworkInterest': {
                'agreementReturned': True,
            },
        }
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'frameworkInterest': {
                'agreementReturned': True,
            },
            'updated_by': 'user',
        }

    def test_unset_framework_agreement_returned(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7",
            json={"frameworkInterest": {"agreementReturned": False}},
            status_code=200)

        result = data_client.unset_framework_agreement_returned(123, 'g-cloud-7', "user")
        assert result == {"frameworkInterest": {"agreementReturned": False}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'frameworkInterest': {'agreementReturned': False},
            'updated_by': 'user'
        }

    def test_update_supplier_framework_agreement_details(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123/frameworks/g-cloud-8",
            json={
                'frameworkInterest': {
                    'agreementDetails': {'signerName': 'name'},
                },
            },
            status_code=200)

        result = data_client.update_supplier_framework_agreement_details(
            123, 'g-cloud-8', {'signerName': 'name'}, "user"
        )
        assert result == {
            'frameworkInterest': {
                'agreementDetails': {'signerName': 'name'}
            },
        }
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'frameworkInterest': {
                'agreementDetails': {'signerName': 'name'}
            },
            'updated_by': 'user',
        }

    def test_register_framework_agreement_countersigned(self, data_client, rmock):
        rmock.post(
            "http://baseurl/suppliers/123/frameworks/g-cloud-7",
            json={"frameworkInterest": {"countersigned": True}},
            status_code=200)

        result = data_client.register_framework_agreement_countersigned(123, 'g-cloud-7', "user")
        assert result == {"frameworkInterest": {"countersigned": True}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'frameworkInterest': {'countersigned': True},
            'updated_by': 'user'
        }

    def test_agree_framework_variation(self, data_client, rmock):
        dummy_response_body = {
            "agreedVariations": {
                "agreedAt": "2016-01-23T12:34:56.000000Z",
                "agreedUserId": 314,
                "agreedUserEmail": "example@digital.gov.uk",
                "agreedUserName": "Paddy Dignam",
            },
        }
        rmock.put(
            "http://baseurl/suppliers/321/frameworks/g-cloud-99/variation/banana-split",
            json=dummy_response_body,
            status_code=200)

        result = data_client.agree_framework_variation(321, 'g-cloud-99', "banana-split", 314, "someuser")
        assert result == dummy_response_body
        assert rmock.called
        assert [rh.json() for rh in rmock.request_history] == [{
            "agreedVariations": {
                "agreedUserId": 314,
            },
            "updated_by": "someuser",
        }]

    def test_find_framework_suppliers(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks/g-cloud-7/suppliers',
            json={'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]},
            status_code=200)

        result = data_client.find_framework_suppliers('g-cloud-7')

        assert result == {'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]}
        assert rmock.called

    def test_find_framework_suppliers_with_agreement_returned(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks/g-cloud-7/suppliers?agreement_returned=True',
            json={'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]},
            status_code=200)

        result = data_client.find_framework_suppliers('g-cloud-7', True)

        assert result == {'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]}
        assert rmock.called

    def test_find_framework_suppliers_with_statuses(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks/g-cloud-7/suppliers?status=signed,on-hold',
            json={'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]},
            status_code=200)

        result = data_client.find_framework_suppliers('g-cloud-7', statuses='signed,on-hold')

        assert result == {'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]}
        assert rmock.called

    def test_find_framework_suppliers_no_declarations(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks/g-cloud-7/suppliers?with_declarations=false',
            json={'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]},
            status_code=200)

        result = data_client.find_framework_suppliers('g-cloud-7', with_declarations=False)

        assert result == {'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]}
        assert rmock.called

    def test_find_framework_suppliers_no_fvra(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks/g-cloud-7/suppliers?with_fvra=false',
            json={'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]},
            status_code=200)

        result = data_client.find_framework_suppliers('g-cloud-7', with_fvra=False)

        assert result == {'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]}
        assert rmock.called

    def test_find_framework_suppliers_with_tac(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks/g-cloud-7/suppliers?with_technical_ability_certificates=true',
            json={'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]},
            status_code=200)

        result = data_client.find_framework_suppliers('g-cloud-7', with_technical_ability_certificates=True)

        assert result == {'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]}
        assert rmock.called

    def test_find_framework_suppliers_with_lot_responses(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks/g-cloud-7/suppliers?with_lot_questions_responses=true',
            json={'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]},
            status_code=200)

        result = data_client.find_framework_suppliers('g-cloud-7', with_lot_questions_responses=True)

        assert result == {'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]}
        assert rmock.called

    def test_find_framework_suppliers_with_lot_pricings(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks/g-cloud-7/suppliers?with_lot_pricings=true',
            json={'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]},
            status_code=200)

        result = data_client.find_framework_suppliers('g-cloud-7', with_lot_pricings=True)

        assert result == {'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]}
        assert rmock.called

    def test_find_framework_suppliers_with_cdp_supplier_information(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks/g-cloud-7/suppliers?with_cdp_supplier_information=true',
            json={'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]},
            status_code=200)

        result = data_client.find_framework_suppliers('g-cloud-7', with_cdp_supplier_information=True)

        assert result == {'supplierFrameworks': [{"agreementReturned": False}, {"agreementReturned": True}]}
        assert rmock.called

    def test_find_supplier_framework_applications_by_lot(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks/g-cloud-7/suppliers/applications?lot=cloud-sourcing',
            json={'supplierFrameworks': [{"supplierId": 1}, {"supplierId": 2}]},
            status_code=200)

        result = data_client.find_supplier_framework_applications_by_lot('g-cloud-7', 'cloud-sourcing')

        assert result == {'supplierFrameworks': [{"supplierId": 1}, {"supplierId": 2}]}
        assert rmock.called

    def test_find_supplier_framework_applications_by_lot_with_attributes(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks/g-cloud-7/suppliers/applications?lot=cloud-sourcing'
            '&evaluation_status=not-evaluated&section_slug=slug-name&evaluator_framework_lot_id=1234',
            json={'supplierFrameworks': [{"supplierId": 1}, {"supplierId": 2}]},
            status_code=200)

        result = data_client.find_supplier_framework_applications_by_lot(
            'g-cloud-7',
            'cloud-sourcing',
            evaluation_status='not-evaluated',
            section_slug='slug-name',
            evaluator_framework_lot_id=1234
        )

        assert result == {'supplierFrameworks': [{"supplierId": 1}, {"supplierId": 2}]}
        assert rmock.called

    def test_verify_supplier_framework_application(self, data_client, rmock):
        rmock.get(
            "http://baseurl/frameworks/g-things-88/suppliers/1234/applications/verify",
            json={"applicationStatus": "result"},
            status_code=200)

        result = data_client.verify_supplier_framework_application('g-things-88', 1234)

        assert result == {"applicationStatus": "result"}
        assert rmock.called

    def test_verify_supplier_framework_application_with_lot(self, data_client, rmock):
        rmock.get(
            "http://baseurl/frameworks/g-things-88/suppliers/1234/applications/verify?lot=g-thing",
            json={"applicationStatus": "result"},
            status_code=200)

        result = data_client.verify_supplier_framework_application('g-things-88', 1234, 'g-thing')

        assert result == {"applicationStatus": "result"}
        assert rmock.called

    def test_can_export_suppliers(self, data_client, rmock):
        rmock.get(
            "http://baseurl/suppliers/export/g-cloud-9",
            json={"suppliers": "result"},
            status_code=200)
        result = data_client.export_suppliers('g-cloud-9')
        assert rmock.called
        assert result == {"suppliers": "result"}

    def test_migrate_framework_application(self, data_client, rmock):
        rmock.post(
            "http://baseurl/frameworks/g-things-88/migrate-application",
            json={"message": "done"},
            status_code=200
        )

        result = data_client.migrate_framework_application('g-things-88', 1234, 4567, 'user')

        assert result == {"message": "done"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'fromSupplierId': 1234,
            'toSupplierId': 4567,
            'updated_by': 'user',
        }


class TestAgreementMethods(object):
    def test_put_signed_agreement_on_hold(self, data_client, rmock):
        rmock.post(
            "http://baseurl/agreements/101/on-hold",
            json={'David made me put data in': True},
            status_code=200
        )

        result = data_client.put_signed_agreement_on_hold(101, 'Chris')

        assert result == {'David made me put data in': True}
        assert rmock.call_count == 1
        assert rmock.last_request.json() == {'updated_by': 'Chris'}

    def test_approve_agreement_for_countersignature(self, data_client, rmock):
        rmock.post(
            "http://baseurl/agreements/101/approve",
            json={'David made me put data in': True},
            status_code=200
        )

        result = data_client.approve_agreement_for_countersignature(101, 'chris@example.com', '1234')

        assert result == {'David made me put data in': True}
        assert rmock.call_count == 1
        assert rmock.last_request.json() == {'updated_by': 'chris@example.com', 'agreement': {'userId': '1234'}}

    def test_unapprove_agreement_for_countersignature(self, data_client, rmock):
        rmock.post(
            "http://baseurl/agreements/7890/approve",
            json={'something_else': 4321},
            status_code=200,
        )

        result = data_client.unapprove_agreement_for_countersignature(7890, 'tactical.shorts@example.com', '6543')

        assert result == {'something_else': 4321}
        assert rmock.call_count == 1
        assert rmock.last_request.json() == {
            'updated_by': 'tactical.shorts@example.com',
            'agreement': {
                'userId': '6543',
                'unapprove': True,
            },
        }


class TestDraftServiceMethods(object):
    def test_find_draft_services(self, data_client, rmock):
        rmock.get(
            "http://baseurl/draft-services?supplier_id=2&service_id=1234567890123456&framework=g-cloud-6",
            json={"draft-services": "result"},
            status_code=200,
        )

        result = data_client.find_draft_services(
            2, service_id='1234567890123456', framework='g-cloud-6')

        assert result == {"draft-services": "result"}
        assert rmock.called

    def test_find_draft_services_by_framework(self, data_client, rmock):
        rmock.get(
            "http://baseurl/draft-services/framework/g-cloud-6",
            json={"draft-services": "result"},
            status_code=200,
        )

        result = data_client.find_draft_services_by_framework('g-cloud-6')

        assert result == {"draft-services": "result"}
        assert rmock.called

    def test_find_draft_services_by_framework_by_page(self, data_client, rmock):
        rmock.get(
            "http://baseurl/draft-services/framework/g-cloud-6?page=123",
            json={"draft-services": "result"},
            status_code=200,
        )

        result = data_client.find_draft_services_by_framework('g-cloud-6', page=123)

        assert result == {"draft-services": "result"}
        assert rmock.called

    def test_find_draft_services_by_framework_with_optional_params(self, data_client, rmock):
        rmock.get(
            "http://baseurl/draft-services/framework/g-cloud-6?status=submitted&supplier_id=2&lot=cloud-support",
            json={"draft-services": "result"},
            status_code=200,
        )

        result = data_client.find_draft_services_by_framework(
            'g-cloud-6', status='submitted', supplier_id=2, lot='cloud-support')

        assert result == {"draft-services": "result"}
        assert rmock.called

    def test_get_draft_service(self, data_client, rmock):
        rmock.get(
            "http://baseurl/draft-services/2",
            json={"draft-services": "result"},
            status_code=200,
        )

        result = data_client.get_draft_service(2)

        assert result == {"draft-services": "result"}
        assert rmock.called

    def test_delete_draft_service(self, data_client, rmock):
        rmock.delete(
            "http://baseurl/draft-services/2",
            json={"done": "it"},
            status_code=200,
        )

        result = data_client.delete_draft_service(
            2, 'user'
        )

        assert result == {"done": "it"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user'
        }

    def test_copy_draft_service_from_existing_service(
            self, data_client, rmock):
        rmock.put(
            "http://baseurl/draft-services/copy-from/2",
            json={"done": "it"},
            status_code=201,
        )

        result = data_client.copy_draft_service_from_existing_service(
            2, 'user', {'some': 'data'}
        )

        assert result == {"done": "it"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
            'some': 'data',
        }

    def test_copy_published_from_framework(
            self, data_client, rmock):
        rmock.post(
            "http://baseurl/draft-services/dos-cloud/sausages/copy-published-from-framework",
            json={"done": "it"},
            status_code=201,
        )

        result = data_client.copy_published_from_framework(
            'dos-cloud', 'sausages', 'user', {'some': 'data'}
        )

        assert result == {"done": "it"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
            'some': 'data',
        }

    def test_copy_draft_service(self, data_client, rmock):
        rmock.post(
            "http://baseurl/draft-services/2/copy",
            json={"done": "copy"},
            status_code=201,
        )

        result = data_client.copy_draft_service(2, 'user')

        assert result == {"done": "copy"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user'
        }

    def test_complete_draft_service(self, data_client, rmock):
        rmock.post(
            "http://baseurl/draft-services/2/complete",
            json={"done": "complete"},
            status_code=201,
        )

        result = data_client.complete_draft_service(2, 'user')

        assert result == {"done": "complete"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user'
        }

    def test_update_draft_service_status(self, data_client, rmock):
        rmock.post(
            "http://baseurl/draft-services/2/update-status",
            json={"services": {"status": "failed"}},
            status_code=200,
        )

        result = data_client.update_draft_service_status(2, 'failed', 'user')

        assert result == {"services": {"status": "failed"}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
            'services': {'status': 'failed'}
        }

    def test_update_draft_service(self, data_client, rmock):
        rmock.post(
            "http://baseurl/draft-services/2",
            json={"done": "it"},
            status_code=200,
        )

        result = data_client.update_draft_service(
            2, {"field": "value"}, 'user'
        )

        assert result == {"done": "it"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'services': {
                "field": "value"
            },
            'updated_by': 'user'
        }

    def test_update_draft_service_with_page_questions(self, data_client, rmock):
        rmock.post(
            "http://baseurl/draft-services/2",
            json={"done": "it"},
            status_code=200,
        )

        result = data_client.update_draft_service(
            2, {"field": "value"}, 'user', ['question1', 'question2']
        )

        assert result == {"done": "it"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'services': {
                "field": "value"
            },
            'updated_by': 'user',
            'page_questions': ['question1', 'question2']
        }

    def test_update_draft_service_with_ignored_fields(self, data_client, rmock):
        rmock.post(
            "http://baseurl/draft-services/2",
            json={"done": "it"},
            status_code=200,
        )

        result = data_client.update_draft_service(
            2, {"field": "value"}, 'user', None, ['question2', 'question3']
        )

        assert result == {"done": "it"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'services': {
                "field": "value"
            },
            'updated_by': 'user',
            'ignored_fields': ['question2', 'question3']
        }

    def test_update_draft_service_with_page_questions_and_ignored_fields(self, data_client, rmock):
        rmock.post(
            "http://baseurl/draft-services/2",
            json={"done": "it"},
            status_code=200,
        )

        result = data_client.update_draft_service(
            2, {"field": "value"}, 'user', ['question1', 'question2'], ['question2', 'question3']
        )

        assert result == {"done": "it"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'services': {
                "field": "value"
            },
            'updated_by': 'user',
            'page_questions': ['question1', 'question2'],
            'ignored_fields': ['question2', 'question3']
        }

    def test_publish_draft_service(self, data_client, rmock):
        rmock.post(
            "http://baseurl/draft-services/2/publish",
            json={"done": "it"},
            status_code=200,
        )

        result = data_client.publish_draft_service(
            2, 'user'
        )

        assert result == {"done": "it"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user'
        }

    def test_create_new_draft_service(self, data_client, rmock):
        rmock.post(
            "http://baseurl/draft-services",
            json={"done": "it"},
            status_code=201,
        )

        result = data_client.create_new_draft_service(
            'g-cloud-7', 'iaas', 2, {'serviceName': 'name'}, 'user',
        )

        assert result == {"done": "it"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'page_questions': [],
            'updated_by': 'user',
            'services': {
                'frameworkSlug': 'g-cloud-7',
                'supplierId': 2,
                'lot': 'iaas',
                'serviceName': 'name',
            }
        }


class TestAuditEventMethods(object):
    def test_get_audit_event(self, data_client, rmock):
        rmock.get(
            "http://baseurl/audit-events/123",
            json={"audit-event": "result"},
            status_code=200,
        )

        result = data_client.get_audit_event(123)

        assert result == {"audit-event": "result"}
        assert rmock.called

    def test_find_audit_events(self, data_client, rmock):
        rmock.get(
            "http://baseurl/audit-events",
            json={"audit-event": "result"},
            status_code=200,
        )

        result = data_client.find_audit_events()

        assert result == {"audit-event": "result"}
        assert rmock.called

    def test_find_audit_events_with_audit_type(self, data_client, rmock):
        rmock.get(
            "http://baseurl/audit-events?audit-type=contact_update",
            json={"audit-event": "result"},
            status_code=200,
        )

        result = data_client.find_audit_events(audit_type=AuditTypes.contact_update)

        assert result == {"audit-event": "result"}
        assert rmock.called

    def test_find_audit_events_with_page_and_type(self, data_client, rmock):
        rmock.get(
            "http://baseurl/audit-events?page=123&audit-type=contact_update",
            json={"audit-event": "result"},
            status_code=200,
        )

        result = data_client.find_audit_events(page=123, audit_type=AuditTypes.contact_update)

        assert result == {"audit-event": "result"}
        assert rmock.called

    def test_find_audit_events_with_custom_page_size(self, data_client, rmock):
        rmock.get(
            "http://baseurl/audit-events?per_page=999",
            json={"audit-event": "result"},
            status_code=200)

        result = data_client.find_audit_events(per_page=999)

        assert result == {"audit-event": "result"}
        assert rmock.called

    def test_find_audit_events_with_data_supplier_id(self, data_client, rmock):
        rmock.get(
            "http://baseurl/audit-events?data-supplier-id=123456",
            json={"audit-event": "result"},
            status_code=200)

        result = data_client.find_audit_events(data_supplier_id=123456)

        assert result == {"audit-event": "result"}
        assert rmock.called

    def test_find_audit_events_with_all_params(self, data_client, rmock):
        url = (
            "http://baseurl/audit-events?object-type=foo&object-id=34&acknowledged=all&latest_first=True"
            "&audit-date=2010-01-01&page=12&audit-type=contact_update&per_page=23&earliest_for_each_object=True"
            "&user=ruby.cohen@example.com&data-supplier-id=123456&sort_by=bar"
        )
        rmock.get(
            url,
            json={"audit-event": "result"},
            status_code=200,
        )

        result = data_client.find_audit_events(
            acknowledged='all',
            audit_date='2010-01-01',
            audit_type=AuditTypes.contact_update,
            data_supplier_id=123456,
            earliest_for_each_object=True,
            latest_first=True,
            page=12,
            per_page=23,
            object_id=34,
            object_type='foo',
            sort_by='bar',
            user="ruby.cohen@example.com")

        assert result == {"audit-event": "result"}
        assert rmock.called

    def test_find_audit_events_with_no_none_params(self, data_client, rmock):
        rmock.get(
            "http://baseurl/audit-events?page=123&audit-type=contact_update&acknowledged=all",
            json={"audit-event": "result"},
            status_code=200,
        )

        result = data_client.find_audit_events(
            page=123,
            audit_type=AuditTypes.contact_update,
            acknowledged='all',
            audit_date=None)

        assert result == {"audit-event": "result"}
        assert rmock.called

    def test_find_audit_events_with_invalid_audit_type(self, data_client, rmock):
        with pytest.raises(TypeError):
            data_client.find_audit_events(
                page=123,
                audit_type="invalid",
                acknowledged='all',
                audit_date=None)

    def test_acknowledge_audit_event(self, data_client, rmock):
        rmock.post(
            "http://baseurl/audit-events/123/acknowledge",
            json={"audit-event": "result"},
            status_code=200,
        )

        result = data_client.acknowledge_audit_event(
            audit_event_id=123,
            user='user')

        assert rmock.called
        assert result == {"audit-event": "result"}
        assert rmock.request_history[0].json() == {
            'updated_by': 'user'
        }

    def test_acknowledge_service_update_including_previous(self, data_client, rmock):
        rmock.post(
            "http://baseurl/services/123/updates/acknowledge",
            json={"auditEvents": [{"id": 120}, {"id": 123}]},
            status_code=200,
        )

        result = data_client.acknowledge_service_update_including_previous(
            service_id=123,
            audit_event_id=456,
            user='user')

        assert rmock.called
        assert result == {"auditEvents": [{"id": 120}, {"id": 123}]}
        assert rmock.request_history[0].json() == {
            "latestAuditEventId": 456,
            'updated_by': 'user'
        }

    def test_create_audit_event(self, data_client, rmock):
        rmock.post(
            "http://baseurl/audit-events",
            json={"auditEvents": "result"},
            status_code=201)

        result = data_client.create_audit_event(
            AuditTypes.contact_update, "a user", {"key": "value"}, "suppliers", "123")

        assert rmock.called
        assert result == {'auditEvents': 'result'}
        assert rmock.request_history[0].json() == {
            "auditEvents": {
                "type": "contact_update",
                "user": "a user",
                "data": {"key": "value"},
                "objectType": "suppliers",
                "objectId": "123",
            }
        }

    def test_create_audit_event_with_no_user(self, data_client, rmock):
        rmock.post(
            "http://baseurl/audit-events",
            json={'auditEvents': 'result'},
            status_code=201)

        result = data_client.create_audit_event(
            AuditTypes.contact_update, None, {'key': 'value'}, 'suppliers', '123')

        assert rmock.called
        assert result == {'auditEvents': 'result'}
        assert rmock.request_history[0].json() == {
            "auditEvents": {
                "type": "contact_update",
                "data": {"key": "value"},
                "objectType": "suppliers",
                "objectId": "123",
            }
        }

    def test_create_audit_event_with_no_object(self, data_client, rmock):
        rmock.post(
            "http://baseurl/audit-events",
            json={'auditEvents': 'result'},
            status_code=201)

        result = data_client.create_audit_event(
            AuditTypes.contact_update, 'user', {'key': 'value'})

        assert rmock.called
        assert result == {'auditEvents': 'result'}
        assert rmock.request_history[0].json() == {
            "auditEvents": {
                "type": "contact_update",
                "user": "user",
                "data": {"key": "value"},
            }
        }

    def test_create_audit_with_no_data_defaults_to_empty_object(self, data_client, rmock):
        rmock.post(
            "http://baseurl/audit-events",
            json={'auditEvents': 'result'},
            status_code=201)

        result = data_client.create_audit_event(AuditTypes.contact_update)

        assert rmock.called
        assert result == {'auditEvents': 'result'}
        assert rmock.request_history[0].json() == {
            "auditEvents": {
                "type": "contact_update",
                "data": {},
            }
        }

    def test_create_audit_event_with_invalid_audit_type(self, data_client, rmock):
        rmock.post(
            "http://baseurl/audit-events",
            json={"auditEvents": "result"},
            status_code=200)

        with pytest.raises(TypeError):
            data_client.create_audit_event(
                "thing_happened", "a user", {"key": "value"}, "suppliers", "123")


class TestFrameworkMethods(object):
    def test_create_framework(self, data_client, rmock):
        rmock.post(
            "http://baseurl/frameworks",
            json={"frameworks": "result"},
            status_code=201,
        )

        result = data_client.create_framework(
            "digital-things-2",
            "Digital Things",
            "digital-things",
            [],
            True,
            False,
            False,
            True,
            False,
            "user@email.com"
        )

        assert result == {"frameworks": "result"}
        assert rmock.last_request.json() == {
            'frameworks': {
                'clarificationQuestionsOpen': False,
                'framework': 'digital-things',
                'hasDirectAward': True,
                'hasFurtherCompetition': False,
                'hasEvaluation': False,
                'hasTechnicalAbilityCertificate': True,
                'hasLotPricing': False,
                'lots': [],
                'name': 'Digital Things',
                'slug': 'digital-things-2',
                'status': 'coming'
            },
            'updated_by': 'user@email.com'
        }

    def test_get_interested_suppliers(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks/g-cloud-11/interest',
            json={'suppliers': [1, 2]},
            status_code=200)

        result = data_client.get_interested_suppliers('g-cloud-11')

        assert result == {'suppliers': [1, 2]}
        assert rmock.called

    def test_get_framework_stats(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks/g-cloud-11/stats',
            json={'drafts': 1},
            status_code=200)

        result = data_client.get_framework_stats('g-cloud-11')

        assert result == {'drafts': 1}
        assert rmock.called

    def test_get_framework_stats_raises_on_error(self, data_client, rmock):
        with pytest.raises(APIError):
            rmock.get(
                'http://baseurl/frameworks/g-cloud-11/stats',
                json={'drafts': 1},
                status_code=400)

            data_client.get_framework_stats('g-cloud-11')

    def test_find_frameworks(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks',
            json={'frameworks': ['g6', 'g7']},
            status_code=200)

        result = data_client.find_frameworks()

        assert result == {'frameworks': ['g6', 'g7']}
        assert rmock.called

    def test_get_framework(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks/g-cloud-11',
            json={'frameworks': {'g-cloud-11': 'yes'}},
            status_code=200)

        result = data_client.get_framework('g-cloud-11')

        assert result == {'frameworks': {'g-cloud-11': 'yes'}}
        assert rmock.called

    def test_update_framework(self, data_client, rmock):
        rmock.post(
            'http://baseurl/frameworks/g-cloud-11',
            json={'frameworks': {'key': 'value'}},
            status_code=200)

        result = data_client.update_framework(framework_slug='g-cloud-11', data={'key': 'value'}, user='me@my.mine')

        assert result == {'frameworks': {'key': 'value'}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            "frameworks": {
                'key': 'value'
            },
            "updated_by": "me@my.mine"
        }

    def test_transition_dos_framework(self, data_client, rmock):
        rmock.post(
            "http://baseurl/frameworks/transition-dos/dos-22",
            json={"returned": "framework"},
            status_code=200
        )

        result = data_client.transition_dos_framework(
            framework_slug="dos-22", expiring_framework_slug="dos-21", user="Clem Fandango"
        )

        assert result == {"returned": "framework"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            "expiringFramework": "dos-21",
            "updated_by": "Clem Fandango",
        }

    def test_update_framework_communication_category(self, data_client, rmock):
        rmock.post(
            'http://baseurl/frameworks/g-cloud-11/communication-category',
            json={'communicationCategories': {'key': 'value'}},
            status_code=200)

        result = data_client.update_framework_communication_category(
            framework_slug='g-cloud-11',
            data={'key': 'value'},
            user='me@my.mine'
        )

        assert result == {'communicationCategories': {'key': 'value'}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            "communicationCategories": {
                'key': 'value'
            },
            "updated_by": "me@my.mine"
        }

    def test_delete_framework_communication_category(self, data_client, rmock):
        rmock.delete(
            'http://baseurl/frameworks/g-cloud-11/communication-category',
            json={'message': 'done'},
            status_code=200)

        result = data_client.delete_framework_communication_category(
            'g-cloud-11',
            'Compliance',
            user='me@my.mine'
        )

        assert result == {'message': 'done'}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            "communicationCategory": "Compliance",
            "updated_by": "me@my.mine"
        }


class TestBriefMethods(object):
    def test_create_brief(self, data_client, rmock):
        rmock.post(
            "http://baseurl/briefs",
            json={"briefs": "result"},
            status_code=201,
        )

        result = data_client.create_brief(
            "digital-things", "digital-watches", 123,
            {"title": "Timex"},
            "user@email.com",
            page_questions=["title"])

        assert result == {"briefs": "result"}
        assert rmock.last_request.json() == {
            "briefs": {
                "frameworkSlug": "digital-things",
                "lot": "digital-watches",
                "userId": 123,
                "title": "Timex"
            },
            "page_questions": ["title"],
            "updated_by": "user@email.com"
        }

    def test_copy_brief(self, data_client, rmock):
        rmock.post(
            "http://baseurl/briefs/123/copy",
            json={"briefs": "result"},
            status_code=201,
        )

        result = data_client.copy_brief(123, "user@email.com")

        assert result == {"briefs": "result"}
        assert rmock.last_request.json() == {
            "updated_by": "user@email.com"
        }

    def test_update_brief(self, data_client, rmock):
        rmock.post(
            "http://baseurl/briefs/123",
            json={"briefs": "result"},
            status_code=200,
        )

        result = data_client.update_brief(123, {"foo": "bar"}, "user@email.com")

        assert result == {"briefs": "result"}
        assert rmock.last_request.json() == {
            "briefs": {"foo": "bar"},
            "page_questions": [],
            "updated_by": "user@email.com"
        }

    def test_update_brief_award_brief_response(self, data_client, rmock):
        rmock.post(
            "http://baseurl/briefs/123/award",
            json={"briefs": "result"},
            status_code=200,
        )

        result = data_client.update_brief_award_brief_response(123, 456, "user@email.com")

        assert result == {"briefs": "result"}
        assert rmock.last_request.json() == {
            "briefResponseId": 456,
            "updated_by": "user@email.com"
        }

    def test_update_brief_award_details(self, data_client, rmock):
        rmock.post(
            "http://baseurl/briefs/123/award/456/contract-details",
            json={"briefs": "result"},
            status_code=200,
        )

        result = data_client.update_brief_award_details(
            123, 456, {"awardedContractStartDate": "2020-12-31", "contractValue": "99.95"}, "user@email.com"
        )

        assert result == {"briefs": "result"}
        assert rmock.last_request.json() == {
            "awardDetails": {
                "awardedContractStartDate": "2020-12-31",
                "contractValue": "99.95",
            },
            "updated_by": "user@email.com"
        }

    def test_unaward_brief_response(self, data_client, rmock):
        rmock.delete(
            "http://baseurl/briefs/123/award/456/contract-details",
            json={"briefs": "result"},
            status_code=200,
        )

        result = data_client.unaward_brief_response(123, 456, updated_by="user@email.com")

        assert result == {"briefs": "result"}
        assert rmock.last_request.json() == {"updated_by": "user@email.com"}

    def test_publish_brief(self, data_client, rmock):
        rmock.post(
            "http://baseurl/briefs/123/publish",
            json={"briefs": "result"},
            status_code=200,
        )

        result = data_client.publish_brief(123, "user@email.com")

        assert result == {"briefs": "result"}
        assert rmock.last_request.json() == {
            "updated_by": "user@email.com"
        }

    def test_cancel_brief(self, data_client, rmock):
        rmock.post(
            "http://baseurl/briefs/123/cancel",
            json={"briefs": "result"},
            status_code=200,
        )

        result = data_client.cancel_brief(123, "user@email.com")

        assert result == {"briefs": "result"}
        assert rmock.last_request.json() == {
            "updated_by": "user@email.com"
        }

    def test_withdraw_brief(self, data_client, rmock):
        rmock.post(
            "http://baseurl/briefs/123/withdraw",
            json={"briefs": "result"},
            status_code=200,
        )

        result = data_client.withdraw_brief(123, "user@email.com")

        assert result == {"briefs": "result"}
        assert rmock.last_request.json() == {
            "updated_by": "user@email.com"
        }

    def test_update_brief_as_unsuccessful(self, data_client, rmock):
        rmock.post(
            "http://baseurl/briefs/123/unsuccessful",
            json={"briefs": "result"},
            status_code=200,
        )

        result = data_client.update_brief_as_unsuccessful(123, "user@email.com")

        assert result == {"briefs": "result"}
        assert rmock.last_request.json() == {
            "updated_by": "user@email.com"
        }

    def test_get_brief(self, data_client, rmock):
        rmock.get(
            "http://baseurl/briefs/123",
            json={"briefs": "result"},
            status_code=200)

        result = data_client.get_brief(123)

        assert result == {"briefs": "result"}

    def test_find_briefs(self, data_client, rmock):
        rmock.get(
            "http://baseurl/briefs?user_id=123",
            json={"briefs": []},
            status_code=200)

        result = data_client.find_briefs(user_id=123)

        assert rmock.called
        assert result == {"briefs": []}

    def test_find_briefs_for_user(self, data_client, rmock):
        rmock.get(
            "http://baseurl/briefs?user_id=123",
            json={"briefs": []},
            status_code=200)

        result = data_client.find_briefs(user_id=123)

        assert rmock.called
        assert result == {"briefs": []}

    def test_find_briefs_by_lot_status_framework_and_human_readable(self, data_client, rmock):
        rmock.get(
            "http://baseurl/briefs?status=live,closed&framework=digital-biscuits&lot=custard-creams&human=true",
            json={"briefs": [{"biscuit": "tasty"}]},
            status_code=200)

        result = data_client.find_briefs(status="live,closed", framework="digital-biscuits", lot="custard-creams",
                                         human=True)

        assert rmock.called
        assert result == {"briefs": [{"biscuit": "tasty"}]}

    def test_find_briefs_with_users(self, data_client, rmock):
        rmock.get(
            "http://baseurl/briefs?with_users=True",
            json={"briefs": [{"biscuit": "tasty"}]},
            status_code=200)

        result = data_client.find_briefs(with_users=True)

        assert rmock.called
        assert result == {"briefs": [{"biscuit": "tasty"}]}

    def test_find_briefs_closed_on_date(self, data_client, rmock):
        rmock.get(
            "http://baseurl/briefs?closed_on=2017-10-20",
            json={"briefs": [{"applicationsClosedAt": "2017-10-20"}]},
            status_code=200)

        result = data_client.find_briefs(closed_on="2017-10-20")

        assert rmock.called
        assert result == {"briefs": [{"applicationsClosedAt": "2017-10-20"}]}

    def test_find_briefs_withdrawn_on_date(self, data_client, rmock):
        rmock.get(
            "http://baseurl/briefs?withdrawn_on=2017-10-20",
            json={"briefs": [{"withdrawnAt": "2017-10-20"}]},
            status_code=200)

        result = data_client.find_briefs(withdrawn_on="2017-10-20")

        assert rmock.called
        assert result == {"briefs": [{"withdrawnAt": "2017-10-20"}]}

    def test_find_briefs_cancelled_on_date(self, data_client, rmock):
        rmock.get(
            "http://baseurl/briefs?cancelled_on=2017-10-20",
            json={"briefs": [{"cancelledAt": "2017-10-20"}]},
            status_code=200)

        result = data_client.find_briefs(cancelled_on="2017-10-20")

        assert rmock.called
        assert result == {"briefs": [{"cancelledAt": "2017-10-20"}]}

    def test_find_briefs_unsuccessful_on_date(self, data_client, rmock):
        rmock.get(
            "http://baseurl/briefs?unsuccessful_on=2017-10-20",
            json={"briefs": [{"unsuccessfulAt": "2017-10-20"}]},
            status_code=200)

        result = data_client.find_briefs(unsuccessful_on="2017-10-20")

        assert rmock.called
        assert result == {"briefs": [{"unsuccessfulAt": "2017-10-20"}]}

    def test_find_briefs_closed_after_date(self, data_client, rmock):
        rmock.get(
            "http://baseurl/briefs?closed_after=2017-10-20",
            json={"briefs": [{"closedAfter": "2017-10-20"}]},
            status_code=200)

        result = data_client.find_briefs(status_date_filters={"closed_after": "2017-10-20"})

        assert rmock.called
        assert result == {"briefs": [{"closedAfter": "2017-10-20"}]}

    def test_find_briefs_with_clarification_questions(self, data_client, rmock):
        rmock.get(
            "http://baseurl/briefs?with_clarification_questions=True",
            json={"briefs": [{"biscuit": "tasty"}]},
            status_code=200)

        result = data_client.find_briefs(with_clarification_questions=True)

        assert rmock.called
        assert result == {"briefs": [{"biscuit": "tasty"}]}

    def test_delete_brief(self, data_client, rmock):
        rmock.delete(
            "http://baseurl/briefs/2",
            json={"done": "it"},
            status_code=200,
        )

        result = data_client.delete_brief(
            2, 'user'
        )

        assert result == {"done": "it"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user'
        }

    def test_is_supplier_eligible_for_brief(self, data_client, rmock):
        rmock.get(
            "http://baseurl/briefs/456/services?supplier_id=123",
            json={"services": ["one"]},
            status_code=200)

        result = data_client.is_supplier_eligible_for_brief(123, 456)

        assert result is True

    def test_supplier_ineligible_for_brief(self, data_client, rmock):
        rmock.get(
            "http://baseurl/briefs/456/services?supplier_id=123",
            json={"services": []},
            status_code=200)

        result = data_client.is_supplier_eligible_for_brief(123, 456)

        assert result is False

    def test_add_brief_clarification_question(self, data_client, rmock):
        rmock.post(
            "http://baseurl/briefs/1/clarification-questions",
            json={"briefs": "result"},
            status_code=200)

        result = data_client.add_brief_clarification_question(1, "Why?", "Because", "user@example.com")

        assert result == {"briefs": "result"}
        assert rmock.last_request.json() == {
            "clarificationQuestion": {"question": "Why?", "answer": "Because"},
            "updated_by": "user@example.com",
        }


class TestBriefResponseMethods(object):
    def test_create_brief_response_with_page_questions(self, data_client, rmock):
        rmock.post(
            "http://baseurl/brief-responses",
            json={"briefs": "result"},
            status_code=201,
        )

        result = data_client.create_brief_response(
            1, 2, {"essentialRequirements": [True, None, False]}, "user@email.com", page_questions=['question']
        )

        assert result == {"briefs": "result"}
        assert rmock.last_request.json() == {
            "briefResponses": {
                "briefId": 1,
                "supplierId": 2,
                "essentialRequirements": [True, None, False],
            },
            "page_questions": ['question'],
            "updated_by": "user@email.com"
        }

    def test_create_brief_response_without_page_questions(self, data_client, rmock):
        rmock.post(
            "http://baseurl/brief-responses",
            json={"briefs": "result"},
            status_code=201,
        )

        result = data_client.create_brief_response(
            1, 2, {"essentialRequirements": [True, None, False]}, "user@email.com"
        )

        assert result == {"briefs": "result"}
        assert rmock.last_request.json() == {
            "briefResponses": {
                "briefId": 1,
                "supplierId": 2,
                "essentialRequirements": [True, None, False],
            },
            "page_questions": [],
            "updated_by": "user@email.com"
        }

    def test_update_brief_response(self, data_client, rmock):
        rmock.post(
            "http://baseurl/brief-responses/1234",
            json={"briefs": "result"},
            status_code=200,
        )

        result = data_client.update_brief_response(
            1234,
            {'email_address': 'test@example.com'},
            'user@example.com',
            ['email_address']
        )

        assert result == {"briefs": "result"}
        assert rmock.last_request.json() == {
            "briefResponses": {
                'email_address': 'test@example.com'
            },
            "page_questions": ['email_address'],
            "updated_by": "user@example.com"
        }

    def test_submit_brief_response(self, data_client, rmock):
        rmock.post(
            "http://baseurl/brief-responses/123/submit",
            json={"briefResponses": "result"},
            status_code=200,
        )

        result = data_client.submit_brief_response(123, "user@email.com")

        assert result == {"briefResponses": "result"}

        assert rmock.last_request.json() == {
            "updated_by": "user@email.com"
        }

    def test_get_brief_response(self, data_client, rmock):
        rmock.get(
            "http://baseurl/brief-responses/123",
            json={"briefResponses": "result"},
            status_code=200)

        result = data_client.get_brief_response(123)

        assert result == {"briefResponses": "result"}

    def test_find_brief_responses(self, data_client, rmock):
        url = (
            "http://baseurl/brief-responses?brief_id=1&supplier_id=2&status=draft&"
            "framework=digital-outcomes-and-specialists-2&awarded_at=2018-01-01&with-data=false"
        )
        rmock.get(
            url,
            json={"briefResponses": []},
            status_code=200)

        result = data_client.find_brief_responses(
            brief_id=1,
            supplier_id=2,
            status='draft',
            framework='digital-outcomes-and-specialists-2',
            awarded_at="2018-01-01",
            with_data=False,
        )

        assert result == {"briefResponses": []}


class TestFrameworkAgreementMethods(object):
    def test_get_framework_agreement(self, data_client, rmock):
        rmock.get(
            "http://baseurl/agreements/12345",
            json={"agreement": {'details': 'here'}},
            status_code=200)

        result = data_client.get_framework_agreement(12345)

        assert result == {"agreement": {'details': 'here'}}

    def test_create_framework_agreement(self, data_client, rmock):
        rmock.post(
            "http://baseurl/agreements",
            json={"agreement": {'details': 'here'}},
            status_code=201)

        result = data_client.create_framework_agreement(
            10,
            'g-cloud-8',
            {
                "signerName": "Rex",
                "signerRole": "Driver of the Aegis"
            },
            "user@example.com"
        )

        assert result == {"agreement": {'details': 'here'}}
        assert rmock.last_request.json() == {
            "agreement": {
                "supplierId": 10,
                "frameworkSlug": "g-cloud-8",
                "signedAgreementDetails": {
                    "signerName": "Rex",
                    "signerRole": "Driver of the Aegis"
                }
            },
            "updated_by": "user@example.com",
        }

    def test_update_framework_agreement(self, data_client, rmock):
        rmock.post(
            "http://baseurl/agreements/12345",
            json={"agreement": {'details': 'here'}},
            status_code=200)

        result = data_client.update_framework_agreement(12345, {"new": "details"}, "user@example.com")

        assert result == {"agreement": {'details': 'here'}}
        assert rmock.last_request.json() == {
            "agreement": {"new": "details"},
            "updated_by": "user@example.com",
        }

    def test_update_framework_agreement_undo_countersign(self, data_client, rmock):
        rmock.post(
            "http://baseurl/agreements/12345/undo-countersign",
            json={},
            status_code=200)

        result = data_client.update_framework_agreement_undo_countersign(12345, "user@example.com")

        assert result == {}
        assert rmock.last_request.json() == {
            "updated_by": "user@example.com",
        }

    def test_sign_framework_agreement_with_no_signed_agreement_details(self, data_client, rmock):
        rmock.post(
            "http://baseurl/agreements/12345/sign",
            json={"agreement": {'response': 'here'}},
            status_code=200)

        result = data_client.sign_framework_agreement(12345, "user@example.com")

        assert result == {"agreement": {'response': 'here'}}
        assert rmock.last_request.json() == {
            "updated_by": "user@example.com",
        }

    def test_sign_framework_agreement_with_signed_agreement_details(self, data_client, rmock):
        rmock.post(
            "http://baseurl/agreements/12345/sign",
            json={"agreement": {'response': 'here'}},
            status_code=200)

        result = data_client.sign_framework_agreement(12345, "user@example.com", {"uploaderUserId": 20})

        assert result == {"agreement": {'response': 'here'}}
        assert rmock.last_request.json() == {
            "agreement": {"signedAgreementDetails": {"uploaderUserId": 20}},
            "updated_by": "user@example.com",
        }


class TestDirectAwardMethods(object):
    @pytest.mark.parametrize(
        'user_id, page, latest_first, with_users, having_outcome, locked, expected_query_string',
        (
            (None, None, None, None, None, None, ''),
            (123, None, None, False, None, None, '?user-id=123'),
            (None, 2, None, False, None, None, '?page=2'),
            (None, None, True, False, None, None, '?latest-first=True'),
            (None, None, None, True, None, None, '?include=users'),
            (None, None, None, None, True, None, '?having-outcome=True'),
            (None, None, None, None, None, True, '?locked=True'),
            (
                123,
                2,
                True,
                True,
                False,
                False,
                '?user-id=123&page=2&latest-first=True&include=users&having-outcome=False&locked=False',
            ),
        ),
    )
    def test_find_direct_award_projects(
        self, data_client, rmock, user_id, page, latest_first, with_users, having_outcome, locked, expected_query_string
    ):
        rmock.get('/direct-award/projects{}'.format(expected_query_string),
                  json={"project": "ok"},
                  status_code=200)

        result = data_client.find_direct_award_projects(
            user_id=user_id,
            page=page,
            latest_first=latest_first,
            with_users=with_users,
            having_outcome=having_outcome,
            locked=locked,
        )
        assert result == {"project": "ok"}

    def test_get_direct_award_project(self, data_client, rmock):
        rmock.get('/direct-award/projects/1',
                  json={"project": "ok"},
                  status_code=200)

        result = data_client.get_direct_award_project(project_id=1)
        assert result == {"project": "ok"}

    def test_create_direct_award_project(self, data_client, rmock):
        rmock.post(
            "http://baseurl/direct-award/projects",
            json={"project": "result"},
            status_code=201,
        )

        result = data_client.create_direct_award_project(user_id=123, user_email="user@email.com",
                                                         project_name="my project")

        assert result == {"project": "result"}
        assert rmock.last_request.json() == {
            "project": {
                "name": "my project",
                "userId": 123
            },
            "updated_by": "user@email.com"
        }

    @pytest.mark.parametrize('user_id, page, active, expected_query_string',
                             (
                                 (None, None, None, ''),
                                 (None, None, True, '?only-active=True'),
                                 (None, None, False, '?only-active=False'),
                                 (123, None, None, '?user-id=123'),
                                 (None, 2, None, '?page=2'),
                                 (None, 2, False, '?page=2&only-active=False'),
                                 (123, 2, True, '?user-id=123&page=2&only-active=True'),
                             ))
    def test_find_direct_award_project_searches(self, data_client, rmock, user_id, page, active, expected_query_string):
        rmock.get('/direct-award/projects/1/searches{}'.format(expected_query_string),
                  json={"searches": "ok"},
                  status_code=200)

        result = data_client.find_direct_award_project_searches(user_id=user_id, project_id=1, page=page,
                                                                only_active=active)
        assert result == {"searches": "ok"}

    def test_create_direct_award_project_search(self, data_client, rmock):
        rmock.post(
            "http://baseurl/direct-award/projects/1/searches",
            json={"search": "result"},
            status_code=201,
        )

        result = data_client.create_direct_award_project_search(user_id=123, user_email="user@email.com",
                                                                project_id=1, search_url="search-url")

        assert result == {"search": "result"}
        assert rmock.last_request.json() == {
            "search": {
                "searchUrl": "search-url",
                "userId": 123
            },
            "updated_by": "user@email.com"
        }

    def test_get_direct_award_project_search(self, data_client, rmock):
        rmock.get('/direct-award/projects/1/searches/2?user-id=123',
                  json={"search": "ok"},
                  status_code=200)

        result = data_client.get_direct_award_project_search(user_id=123, project_id=1, search_id=2)
        assert result == {"search": "ok"}

    def test_lock_direct_award_project(self, data_client, rmock):
        rmock.post('/direct-award/projects/1/lock',
                   json={"project": "ok"},
                   status_code=200)

        result = data_client.lock_direct_award_project(user_email="user@email.com", project_id=1)

        assert result == {"project": "ok"}
        assert rmock.last_request.json() == {
            "updated_by": "user@email.com"
        }

    def test_record_direct_award_project_download(self, data_client, rmock):
        rmock.post('/direct-award/projects/1/record-download',
                   json={"project": "ok"},
                   status_code=200)

        result = data_client.record_direct_award_project_download(user_email="user@email.com", project_id=1)

        assert result == {"project": "ok"}
        assert rmock.last_request.json() == {
            "updated_by": "user@email.com"
        }

    def test_create_direct_award_project_outcome_award(self, data_client, rmock):
        rmock.post(
            '/direct-award/projects/31415/services/271C/award',
            json={"outcome": "ok"},
            status_code=200,
        )

        result = data_client.create_direct_award_project_outcome_award(
            user_email="user@email.com",
            project_id=31415,
            awarded_service_id="271C",
        )

        assert result == {"outcome": "ok"}
        assert rmock.last_request.json() == {
            "updated_by": "user@email.com"
        }

    def test_create_direct_award_project_outcome_none_suitable(self, data_client, rmock):
        rmock.post(
            '/direct-award/projects/31415/none-suitable',
            json={"outcome": "ok"},
            status_code=200,
        )

        result = data_client.create_direct_award_project_outcome_none_suitable(
            user_email="user@email.com",
            project_id=31415,
        )

        assert result == {"outcome": "ok"}
        assert rmock.last_request.json() == {
            "updated_by": "user@email.com"
        }

    def test_create_direct_award_project_outcome_cancelled(self, data_client, rmock):
        rmock.post(
            '/direct-award/projects/31415/cancel',
            json={"outcome": "ok"},
            status_code=200,
        )

        result = data_client.create_direct_award_project_outcome_cancelled(
            user_email="user@email.com",
            project_id=31415,
        )

        assert result == {"outcome": "ok"}
        assert rmock.last_request.json() == {
            "updated_by": "user@email.com"
        }

    def test_mark_direct_award_project_as_still_assessing(self, data_client, rmock):
        rmock.patch(
            '/direct-award/projects/31415',
            json={'project': 'ok'},
            status_code=200,
        )

        result = data_client.mark_direct_award_project_as_still_assessing(
            user_email="user@email.com",
            project_id=31415,
        )

        assert result == {"project": "ok"}
        assert rmock.last_request.json() == {
            "project": {
                "stillAssessing": True,
            },
            "updated_by": "user@email.com"
        }

    def test_update_direct_award_project(self, data_client, rmock):
        rmock.patch(
            '/direct-award/projects/31415',
            json={'project': 'ok'},
            status_code=200,
        )

        result = data_client.update_direct_award_project(
            user_email="user@email.com",
            project_id=31415,
            project_data={
                'foo': 'baa',
            }
        )

        assert result == {"project": "ok"}
        assert rmock.last_request.json() == {
            "project": {
                "foo": 'baa',
            },
            "updated_by": "user@email.com"
        }


class TestOutcomeMethods(object):
    def test_update_outcome(self, data_client, rmock):
        rmock.put(
            '/outcomes/314159',
            json={"outcome": "ok"},
            status_code=200,
        )

        data = {
            "completed": True,
            "whosAstanding": {
                "proudPosessor": "damnall",
            },
        }

        result = data_client.update_outcome(
            outcome_id="314159",
            outcome_data=data.copy(),
            user_email="user@email.com",
        )

        assert result == {"outcome": "ok"}
        assert rmock.last_request.json() == {
            "outcome": data,
            "updated_by": "user@email.com"
        }

    def test_find_outcomes(self, data_client, rmock):
        rmock.get(
            "http://baseurl/outcomes?page=2&completed=false",
            json={"outcomes": []},
            status_code=200,
        )

        result = data_client.find_outcomes(page=2, completed=False)

        assert result == {"outcomes": []}


class TestDataAPIClientIterMethods(object):
    def _test_find_iter(self, data_client, rmock, method_name, model_name, url_path, iter_kwargs={}):
        rmock.get(
            'http://baseurl/{}'.format(url_path),
            json={
                'links': {'next': 'http://baseurl/{}?page=2'.format(url_path)},
                model_name: [{'id': 1}, {'id': 2}]
            },
            status_code=200)
        rmock.get(
            'http://baseurl/{}?page=2'.format(url_path),
            json={
                'links': {'prev': 'http://baseurl/{}'.format(url_path)},
                model_name: [{'id': 3}]
            },
            status_code=200)

        result = getattr(data_client, method_name)(**iter_kwargs)
        results = list(result)

        assert len(results) == 3
        assert results[0]['id'] == 1
        assert results[1]['id'] == 2
        assert results[2]['id'] == 3

        # Also check the case that we don't fall over if the API does not give us a `links` dict as part of it's
        # response
        rmock.get(
            'http://baseurl/{}'.format(url_path),
            json={
                model_name: [{'id': 1}, {'id': 2}]
            },
            status_code=200)
        result = getattr(data_client, method_name)(**iter_kwargs)
        results = list(result)

        assert len(results) == 2
        assert results[0]['id'] == 1
        assert results[1]['id'] == 2

    def test_find_users_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_users_iter',
            model_name='users',
            url_path='users')

    def test_find_briefs_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_briefs_iter',
            model_name='briefs',
            url_path='briefs')

    def test_find_brief_responses_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_brief_responses_iter',
            model_name='briefResponses',
            url_path='brief-responses')

    def test_find_audit_events_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_audit_events_iter',
            model_name='auditEvents',
            url_path='audit-events')

    def test_find_suppliers_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_suppliers_iter',
            model_name='suppliers',
            url_path='suppliers')

    def test_find_framework_suppliers_iter(self, data_client, rmock):
        rmock.get(
            'http://baseurl/frameworks/g-cloud-8/suppliers',
            json={
                'links': {'next': 'http://baseurl/frameworks/g-cloud-8/suppliers?page=2'},
                'supplierFrameworks': [{'id': 1}, {'id': 2}]
            },
            status_code=200)
        rmock.get(
            'http://baseurl/frameworks/g-cloud-8/suppliers?page=2',
            json={
                'links': {'prev': 'http://baseurl/frameworks/g-cloud-8/suppliers'},
                'supplierFrameworks': [{'id': 3}]
            },
            status_code=200)

        result = data_client.find_framework_suppliers_iter('g-cloud-8')
        results = list(result)

        assert len(results) == 3
        assert results[0]['id'] == 1
        assert results[1]['id'] == 2
        assert results[2]['id'] == 3

    def test_find_draft_services_iter(self, data_client, rmock):
        rmock.get(
            'http://baseurl/draft-services?supplier_id=123',
            json={
                'links': {'next': 'http://baseurl/draft-services?supplier_id=123&page=2'},
                'services': [{'id': 1}, {'id': 2}]
            },
            status_code=200)
        rmock.get(
            'http://baseurl/draft-services?supplier_id=123&page=2',
            json={
                'links': {'prev': 'http://baseurl/draft-services?supplier_id=123'},
                'services': [{'id': 3}]
            },
            status_code=200)

        result = data_client.find_draft_services_iter(123)
        results = list(result)

        assert len(results) == 3
        assert results[0]['id'] == 1
        assert results[1]['id'] == 2
        assert results[2]['id'] == 3

    def test_find_draft_services_by_framework_iter(self, data_client, rmock):
        rmock.get(
            'http://baseurl/draft-services/framework/g-cloud-12?status=submitted',
            json={
                'links': {'next': 'http://baseurl/draft-services/framework/g-cloud-12?status=submitted&page=2'},
                'services': [{'foo': 'bar'}, {'foo': 'bat'}]
            },
            status_code=200)
        rmock.get(
            'http://baseurl/draft-services/framework/g-cloud-12?status=submitted&page=2',
            json={
                'links': {'prev': 'http://baseurl/draft-services/framework/g-cloud-12?status=submitted'},
                'services': [{'foo': 'baz'}]
            },
            status_code=200)

        result = data_client.find_draft_services_by_framework_iter('g-cloud-12', status='submitted')

        results = list(result)

        assert len(results) == 3
        assert results[0]['foo'] == 'bar'
        assert results[1]['foo'] == 'bat'
        assert results[2]['foo'] == 'baz'

    def test_find_services_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_services_iter',
            model_name='services',
            url_path='services')

    def test_find_services_iter_additional_arguments(self, data_client, rmock):
        rmock.get(
            'http://baseurl/services?supplier_id=123',
            json={
                'links': {},
                'services': [{'id': 1}, {'id': 2}]
            },
            status_code=200)

        result = data_client.find_services_iter(123)
        results = list(result)

        assert len(results) == 2

    def test_find_direct_award_projects_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_direct_award_projects_iter',
            model_name='projects',
            url_path='direct-award/projects')

    @pytest.mark.parametrize('url_path, iter_kwargs',
                             (
                                 ('direct-award/projects/1/searches', {'project_id': 1}),
                                 ('direct-award/projects/1/searches?user-id=123', {'project_id': 1, 'user_id': 123}),
                             ))
    def test_find_direct_award_project_searches_iter(self, data_client, rmock, url_path, iter_kwargs):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_direct_award_project_searches_iter',
            model_name='searches',
            url_path=url_path,
            iter_kwargs=iter_kwargs
        )

    def test_get_direct_award_project_services(self, data_client, rmock):
        rmock.get('/direct-award/projects/1/services',
                  json={"services": "ok"},
                  status_code=200)

        result = data_client.find_direct_award_project_services(project_id=1)
        assert result == {"services": "ok"}

    def test_get_direct_award_project_services_specific_fields(self, data_client, rmock):
        rmock.get('/direct-award/projects/1/services?user-id=123&fields=id,price',
                  json={"services": "ok"},
                  status_code=200)

        result = data_client.find_direct_award_project_services(user_id=123, project_id=1, fields=['id', 'price'])
        assert result == {"services": "ok"}

    def test_find_direct_award_project_services_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_direct_award_project_services_iter',
            model_name='services',
            url_path='direct-award/projects/1/services',
            iter_kwargs={'project_id': 1}
        )

    def test_export_users_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='export_users_iter',
            model_name='users',
            url_path='users/export/g-cloud-9',
            iter_kwargs={'framework_slug': 'g-cloud-9'}
        )

    def test_export_suppliers_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='export_suppliers_iter',
            model_name='suppliers',
            url_path='suppliers/export/g-cloud-9',
            iter_kwargs={'framework_slug': 'g-cloud-9'}
        )

    def test_find_outcomes_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_outcomes_iter',
            model_name='outcomes',
            url_path='outcomes',
            iter_kwargs={},
        )

    def test_get_buyer_email_domains_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name="get_buyer_email_domains_iter",
            model_name="buyerEmailDomains",
            url_path="buyer-email-domains",
            iter_kwargs={},
        )

    def test_find_communications_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_communications_iter',
            model_name='communications',
            url_path='communications',
            iter_kwargs={}
        )

    def test_find_communications_iter_additional_arguments(self, data_client, rmock):
        rmock.get(
            'http://baseurl/communications?framework=g-cloud-6&supplier_id=123',
            json={
                'links': {},
                'communications': [{'id': 1}, {'id': 2}]
            },
            status_code=200)

        result = data_client.find_communications_iter(framework='g-cloud-6', supplier_id=123)
        results = list(result)

        assert len(results) == 2

    def test_find_lot_questions_responses_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_lot_questions_responses_iter',
            model_name='lotQuestionsResponses',
            url_path='lot-questions-responses?framework=g-cloud-6&supplier_id=1234',
            iter_kwargs={
                'supplier_id': 1234,
                'framework_slug': 'g-cloud-6'
            }
        )

    def test_find_lot_questions_responses_applicants_for_framework_lot_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_lot_questions_responses_applicants_for_framework_lot_iter',
            model_name='lotQuestionsResponses',
            url_path='lot-questions-responses/applications?framework=g-cloud-6&lot=g-lot',
            iter_kwargs={
                'framework_slug': 'g-cloud-6',
                'lot_slug': 'g-lot'
            }
        )

    def test_find_evaluator_framework_lots_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_evaluator_framework_lots_iter',
            model_name='evaluatorFrameworkLots',
            url_path='evaluations/evaluator-framework-lots?framework=g-cloud-6&lot=g-things&assigned=True',
            iter_kwargs={
                'framework': 'g-cloud-6',
                'lot': 'g-things'
            }
        )

    def test_find_evaluator_framework_lots_iter_additional_arguments(self, data_client, rmock):
        rmock.get(
            'http://baseurl/evaluations/evaluator-framework-lots?'
            'framework=g-cloud-6&lot=g-things&assigned=True&user_id=123',
            json={
                'links': {},
                'evaluatorFrameworkLots': [{'id': 1}, {'id': 2}]
            },
            status_code=200)

        result = data_client.find_evaluator_framework_lots_iter('g-cloud-6', 'g-things', user_id=123)
        results = list(result)

        assert len(results) == 2

    def test_find_evaluator_framework_lot_sections_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_evaluator_framework_lot_sections_iter',
            model_name='evaluatorFrameworkLotSections',
            url_path='evaluations/evaluator-framework-lot-sections?framework=g-cloud-6&lot=g-things&assigned=True',
            iter_kwargs={
                'framework': 'g-cloud-6',
                'lot': 'g-things'
            }
        )

    def test_find_evaluator_framework_lot_sections_iter_additional_arguments(self, data_client, rmock):
        rmock.get(
            'http://baseurl/evaluations/evaluator-framework-lot-sections?'
            'framework=g-cloud-6&lot=g-things&assigned=True&section_slug=the-slug',
            json={
                'links': {},
                'evaluatorFrameworkLotSections': [{'id': 1}, {'id': 2}]
            },
            status_code=200)

        result = data_client.find_evaluator_framework_lot_sections_iter(
            'g-cloud-6',
            'g-things',
            section_slug='the-slug'
        )
        results = list(result)

        assert len(results) == 2

    def test_find_evaluator_framework_lot_section_evaluations_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_evaluator_framework_lot_section_evaluations_iter',
            model_name='evaluatorFrameworkLotSectionEvaluations',
            url_path='evaluations/evaluator-framework-lot-section-evaluations?framework=g-cloud-6&lot=g-things',
            iter_kwargs={
                'framework': 'g-cloud-6',
                'lot': 'g-things'
            }
        )

    def test_find_evaluator_framework_lot_section_evaluations_iter_additional_arguments(self, data_client, rmock):
        rmock.get(
            'http://baseurl/evaluations/evaluator-framework-lot-section-evaluations?'
            'framework=g-cloud-6&lot=g-things&section_slug=the-slug',
            json={
                'links': {},
                'evaluatorFrameworkLotSectionEvaluations': [{'id': 1}, {'id': 2}]
            },
            status_code=200)

        result = data_client.find_evaluator_framework_lot_section_evaluations_iter(
            'g-cloud-6',
            'g-things',
            section_slug='the-slug'
        )
        results = list(result)

        assert len(results) == 2

    def test_find_supplier_framework_applications_by_lot_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_supplier_framework_applications_by_lot_iter',
            model_name='supplierFrameworks',
            url_path='frameworks/g-cloud-6/suppliers/applications?lot=g-things',
            iter_kwargs={
                'framework_slug': 'g-cloud-6',
                'lot_slug': 'g-things',
            }
        )

    def test_find_lot_questions_response_section_evaluations_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_lot_questions_response_section_evaluations_iter',
            model_name='lotQuestionsResponseSectionEvaluations',
            url_path='lot-questions-response-section-evaluations?framework=g-cloud-6&lot=g-things',
            iter_kwargs={
                'framework': 'g-cloud-6',
                'lot': 'g-things'
            }
        )

    def test_find_lot_questions_response_section_evaluations_iter_additional_arguments(self, data_client, rmock):
        rmock.get(
            'http://baseurl/lot-questions-response-section-evaluations?framework=g-cloud-6&lot=g-things'
            '&section_slug=the-slug',
            json={
                'links': {},
                'lotQuestionsResponseSectionEvaluations': [{'id': 1}, {'id': 2}]
            },
            status_code=200)

        result = data_client.find_lot_questions_response_section_evaluations(
            'g-cloud-6',
            'g-things',
            section_slug='the-slug'
        )
        results = list(result)

        assert len(results) == 2

    def test_find_technical_ability_certificates_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_technical_ability_certificates_iter',
            model_name='technicalAbilityCertificates',
            url_path='technical-ability-certificates?framework=g-cloud-6&supplier_id=1234',
            iter_kwargs={
                'supplier_id': 1234,
                'framework_slug': 'g-cloud-6'
            }
        )

    def test_find_lot_pricings_iter(self, data_client, rmock):
        self._test_find_iter(
            data_client, rmock,
            method_name='find_lot_pricings_iter',
            model_name='lotPricings',
            url_path='lot-pricings?framework=g-cloud-6&supplier_id=1234',
            iter_kwargs={
                'supplier_id': 1234,
                'framework_slug': 'g-cloud-6'
            }
        )


class TestCommunicationsMethods(object):
    def test_find_communications(self, data_client, rmock):
        rmock.get(
            "http://baseurl/communications",
            json={"communications": "result"},
            status_code=200)

        result = data_client.find_communications()

        assert result == {"communications": "result"}
        assert rmock.called

    def test_find_communications_adds_page_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/communications?page=2",
            json={"communications": "result"},
            status_code=200)

        result = data_client.find_communications(page=2)

        assert result == {"communications": "result"}
        assert rmock.called

    def test_find_communications_adds_framework_parameter(
            self, data_client, rmock):
        rmock.get(
            "http://baseurl/communications?framework=g-cloud-6",
            json={"communications": "result"},
            status_code=200)

        result = data_client.find_communications(framework='g-cloud-6')

        assert result == {"communications": "result"}
        assert rmock.called

    def test_find_communications_adds_supplier_id_parameter(
            self, data_client, rmock):
        rmock.get(
            "http://baseurl/communications?supplier_id=1",
            json={"communications": "result"},
            status_code=200)

        result = data_client.find_communications(supplier_id=1)

        assert result == {"communications": "result"}
        assert rmock.called

    def test_find_communications_adds_resolved_parameter(
            self, data_client, rmock):
        rmock.get(
            "http://baseurl/communications?resolved=true",
            json={"communications": "result"},
            status_code=200)

        result = data_client.find_communications(resolved=True)

        assert result == {"communications": "result"}
        assert rmock.called

    def test_find_communications_adds_resolution_parameter(
            self, data_client, rmock):
        rmock.get(
            "http://baseurl/communications?resolution=archived",
            json={"communications": "result"},
            status_code=200)

        result = data_client.find_communications(resolution="archived")

        assert result == {"communications": "result"}
        assert rmock.called

    def test_find_communications_adds_supplier_id_and_resolved_parameter(
            self, data_client, rmock):
        rmock.get(
            "http://baseurl/communications?supplier_id=1&resolved=true",
            json={"communications": "result"},
            status_code=200)

        result = data_client.find_communications(supplier_id=1, resolved=True)

        assert result == {"communications": "result"}
        assert rmock.called

    def test_find_communications_adds_category_parameter(
            self, data_client, rmock):
        rmock.get(
            "http://baseurl/communications?category=Compliance",
            json={"communications": "result"},
            status_code=200)

        result = data_client.find_communications(category="Compliance")

        assert result == {"communications": "result"}
        assert rmock.called

    def test_find_communications_adds_subject_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/communications?subject=Default Subject",
            json={"communications": "result"},
            status_code=200)

        result = data_client.find_communications(subject='Default Subject')

        assert result == {"communications": "result"}
        assert rmock.called

    def test_find_communications_adds_supplier_name_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/communications?supplier_name=Supplier 1",
            json={"communications": "result"},
            status_code=200)

        result = data_client.find_communications(supplier_name="Supplier 1")

        assert result == {"communications": "result"}
        assert rmock.called

    def test_find_communications_adds_message_text_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/communications?message_text=This is",
            json={"communications": "result"},
            status_code=200)

        result = data_client.find_communications(message_text="This is")

        assert result == {"communications": "result"}
        assert rmock.called

    def test_find_communications_adds_sort_by_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/communications?sort_by=supplier_name%3Aasc",
            json={"communications": "result"},
            status_code=200)

        result = data_client.find_communications(sort_by="supplier_name:asc")

        assert result == {"communications": "result"}
        assert rmock.called

    def test_get_communication(self, data_client, rmock):
        rmock.get(
            "http://baseurl/communications/123",
            json={"communications": "result"},
            status_code=200)

        result = data_client.get_communication(123)

        assert result == {"communications": "result"}
        assert rmock.called

    def test_get_communication_should_return_404(self, data_client, rmock):
        rmock.get(
            "http://baseurl/communications/123",
            status_code=404)

        try:
            data_client.get_communication(123)
        except HTTPError:
            assert rmock.called

    def test_update_communication(self, data_client, rmock):
        rmock.post(
            "http://baseurl/communications/123",
            json={"communications": "result"},
            status_code=201,
        )

        result = data_client.update_communication(123, {"foo": "bar"}, 'admin')

        assert result == {"communications": "result"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'communications': {'foo': 'bar'}, 'updated_by': 'admin'
        }

    def test_resolve_communication(self, data_client, rmock):
        rmock.post(
            "http://baseurl/communications/123/resolve",
            json={"message": "done"},
            status_code=200,
        )

        result = data_client.resolve_communication(
            123,
            456,
            'archived',
            "test@example.com"
        )

        assert result == {"message": "done"}
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "resolvedByUserId": 456,
            "resolution": 'archived',
        }

    def test_undo_resolve_communication(self, data_client, rmock):
        rmock.post(
            "http://baseurl/communications/123/undo-resolve",
            json={"message": "done"},
            status_code=200,
        )

        result = data_client.undo_resolve_communication(
            123,
            "test@example.com"
        )

        assert result == {"message": "done"}
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
        }

    def test_read_communication_message(self, data_client, rmock):
        rmock.post(
            "http://baseurl/communications/messages/123/read",
            json={"message": "done"},
            status_code=200,
        )

        result = data_client.read_communication_message(
            123,
            456,
            "test@example.com"
        )

        assert result == {"message": "done"}
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "readByUserId": 456
        }

    def test_create_communication_message(self, data_client, rmock):
        rmock.post(
            "http://baseurl/communications/123/messages",
            json={"communicationMessages": {
                'id': 1,
                'communicationId': 123,
                'text': 'Message text',
                'sentAt': '2024-03-14T00:00:00.000000Z',
                'sentByUserId': 123,
                'sentByUserEmail': 'test+123@digital.gov.uk',
                'target': 'for_admin',
                'attachments': []
            }},
            status_code=201,
        )

        result = data_client.create_communication_message(
            123,
            {
                'text': 'Message text',
                'sentByUserId': 123,
                'target': 'for_admin',
            },
            user="test@example.com"
        )

        assert result == {
            "communicationMessages": {
                'id': 1,
                'communicationId': 123,
                'text': 'Message text',
                'sentAt': '2024-03-14T00:00:00.000000Z',
                'sentByUserId': 123,
                'sentByUserEmail': 'test+123@digital.gov.uk',
                'target': 'for_admin',
                'attachments': []
            }
        }
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "communicationMessages": {
                'text': 'Message text',
                'sentByUserId': 123,
                'target': 'for_admin',
            }
        }

    def test_create_communication_message_with_attachment(self, data_client, rmock):
        rmock.post(
            "http://baseurl/communications/123/messages",
            json={"communicationMessages": {
                'id': 1,
                'communicationId': 123,
                'text': 'Message text',
                'sentAt': '2024-03-14T00:00:00.000000Z',
                'sentByUserId': 123,
                'sentByUserEmail': 'test+123@digital.gov.uk',
                'target': 'for_admin',
                'attachments': [
                    {
                        "id": 1,
                        "communicationMessageId": 1,
                        "filePath": "Attachment_1.pdf",
                    },
                    {
                        "id": 2,
                        "communicationMessageId": 1,
                        "filePath": "Attachment_2.pdf",
                    },
                ]
            }},
            status_code=201,
        )

        result = data_client.create_communication_message(
            123,
            {
                'text': 'Message text',
                'sentByUserId': 123,
                'target': 'for_admin',
            },
            [
                {
                    "filePath": "Attachment_1.pdf",
                },
                {
                    "filePath": "Attachment_2.pdf",
                }
            ],
            user="test@example.com"
        )

        assert result == {
            "communicationMessages": {
                'id': 1,
                'communicationId': 123,
                'text': 'Message text',
                'sentAt': '2024-03-14T00:00:00.000000Z',
                'sentByUserId': 123,
                'sentByUserEmail': 'test+123@digital.gov.uk',
                'target': 'for_admin',
                'attachments': [
                    {
                        "id": 1,
                        "communicationMessageId": 1,
                        "filePath": "Attachment_1.pdf",
                    },
                    {
                        "id": 2,
                        "communicationMessageId": 1,
                        "filePath": "Attachment_2.pdf",
                    },
                ]
            }
        }
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "communicationMessages": {
                'text': 'Message text',
                'sentByUserId': 123,
                'target': 'for_admin',
                'attachments': [
                    {
                        "filePath": "Attachment_1.pdf",
                    },
                    {
                        "filePath": "Attachment_2.pdf",
                    }
                ]
            }
        }

    def test_create_communication(self, data_client, rmock):
        rmock.post(
            "http://baseurl/communications",
            json={"communications": {
                'id': 123,
                'subject': 'Subject text',
                'category': 'Compliance',
                'supplierId': 0,
                'supplierName': "Supplier 0",
                'frameworkSlug': 'g-cloud-6',
                'frameworkFramework': 'g-cloud',
                'frameworkFamily': 'g-cloud',
                'frameworkName': 'G-Cloud 6',
                'frameworkStatus': 'pending',
                'createdAt': '2024-03-14T00:00:00.000000Z',
                'updatedAt': '2024-03-14T00:00:00.000000Z',
                'messages': [
                    {
                        'id': 1,
                        'communicationId': 123,
                        'text': 'Message text',
                        'sentAt': '2024-03-14T00:00:00.000000Z',
                        'sentByUserId': 456,
                        'sentByUserEmail': 'test+456@digital.cabinet-office.gov.uk',
                        'target': 'for_supplier',
                        'attachments': []
                    }
                ]
            }},
            status_code=201,
        )

        result = data_client.create_communication(
            0,
            'g-cloud-6',
            'Compliance',
            'Subject text',
            {
                'text': 'Message text',
                'sentByUserId': 123,
            },
            user="test@example.com"
        )

        assert result == {
            "communications": {
                'id': 123,
                'subject': 'Subject text',
                'category': 'Compliance',
                'supplierId': 0,
                'supplierName': "Supplier 0",
                'frameworkSlug': 'g-cloud-6',
                'frameworkFramework': 'g-cloud',
                'frameworkFamily': 'g-cloud',
                'frameworkName': 'G-Cloud 6',
                'frameworkStatus': 'pending',
                'createdAt': '2024-03-14T00:00:00.000000Z',
                'updatedAt': '2024-03-14T00:00:00.000000Z',
                'messages': [
                    {
                        'id': 1,
                        'communicationId': 123,
                        'text': 'Message text',
                        'sentAt': '2024-03-14T00:00:00.000000Z',
                        'sentByUserId': 456,
                        'sentByUserEmail': 'test+456@digital.cabinet-office.gov.uk',
                        'target': 'for_supplier',
                        'attachments': []
                    }
                ]
            }
        }
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "communications": {
                "supplierId": 0,
                "frameworkSlug": 'g-cloud-6',
                'category': 'Compliance',
                "subject": 'Subject text',
                'messages': {
                    'text': 'Message text',
                    'sentByUserId': 123,
                }
            }
        }

    def test_create_communication_with_attachment(self, data_client, rmock):
        rmock.post(
            "http://baseurl/communications",
            json={"communications": {
                'id': 123,
                'subject': 'Subject text',
                'category': 'Compliance',
                'supplierId': 0,
                'supplierName': "Supplier 0",
                'frameworkSlug': 'g-cloud-6',
                'frameworkFramework': 'g-cloud',
                'frameworkFamily': 'g-cloud',
                'frameworkName': 'G-Cloud 6',
                'frameworkStatus': 'pending',
                'createdAt': '2024-03-14T00:00:00.000000Z',
                'updatedAt': '2024-03-14T00:00:00.000000Z',
                'messages': [
                    {
                        'id': 1,
                        'communicationId': 123,
                        'text': 'Message text',
                        'sentAt': '2024-03-14T00:00:00.000000Z',
                        'sentByUserId': 456,
                        'sentByUserEmail': 'test+456@digital.cabinet-office.gov.uk',
                        'target': 'for_admin',
                        'attachments': [
                            {
                                "id": 1,
                                "communicationMessageId": 1,
                                "filePath": "Attachment_1.pdf",
                            },
                            {
                                "id": 2,
                                "communicationMessageId": 1,
                                "filePath": "Attachment_2.pdf",
                            },
                        ]
                    }
                ]
            }},
            status_code=201,
        )

        result = data_client.create_communication(
            0,
            'g-cloud-6',
            'Compliance',
            'Subject text',
            {
                'text': 'Message text',
                'sentByUserId': 123,
            },
            [
                {
                    "filePath": "Attachment_1.pdf",
                },
                {
                    "filePath": "Attachment_2.pdf",
                }
            ],
            user="test@example.com"
        )

        assert result == {
            "communications": {
                'id': 123,
                'subject': 'Subject text',
                'category': 'Compliance',
                'supplierId': 0,
                'supplierName': "Supplier 0",
                'frameworkSlug': 'g-cloud-6',
                'frameworkFramework': 'g-cloud',
                'frameworkFamily': 'g-cloud',
                'frameworkName': 'G-Cloud 6',
                'frameworkStatus': 'pending',
                'createdAt': '2024-03-14T00:00:00.000000Z',
                'updatedAt': '2024-03-14T00:00:00.000000Z',
                'messages': [
                    {
                        'id': 1,
                        'communicationId': 123,
                        'text': 'Message text',
                        'sentAt': '2024-03-14T00:00:00.000000Z',
                        'sentByUserId': 456,
                        'sentByUserEmail': 'test+456@digital.cabinet-office.gov.uk',
                        'target': 'for_admin',
                        'attachments': [
                            {
                                "id": 1,
                                "communicationMessageId": 1,
                                "filePath": "Attachment_1.pdf",
                            },
                            {
                                "id": 2,
                                "communicationMessageId": 1,
                                "filePath": "Attachment_2.pdf",
                            },
                        ]
                    }
                ]
            }
        }
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "communications": {
                "supplierId": 0,
                "frameworkSlug": 'g-cloud-6',
                "subject": 'Subject text',
                'category': 'Compliance',
                'messages': {
                    'text': 'Message text',
                    'sentByUserId': 123,
                    'attachments': [
                        {
                            "filePath": "Attachment_1.pdf",
                        },
                        {
                            "filePath": "Attachment_2.pdf",
                        }
                    ]
                }
            }
        }

    def test_get_framework_communication_categories(self, data_client, rmock):
        rmock.get(
            "http://baseurl/communications/g-things-97/categories",
            json={"communicationCategories": "result"},
            status_code=200
        )

        result = data_client.get_framework_communication_categories('g-things-97')

        assert result == {"communicationCategories": "result"}
        assert rmock.called


class TestSystemMessagesMethods(object):
    def test_get_system_message(self, data_client, rmock):
        rmock.get(
            "http://baseurl/system-messages/test-system-message",
            json={"systemMessages": "result"},
            status_code=200)

        result = data_client.get_system_message("test-system-message")

        assert result == {"systemMessages": "result"}
        assert rmock.called

    def test_get_system_message_should_return_404(self, data_client, rmock):
        rmock.get(
            "http://baseurl/system-messages/test-system-message",
            status_code=404)

        try:
            data_client.get_system_message("test-system-message")
        except HTTPError:
            assert rmock.called

    def test_create_system_message(self, data_client, rmock):
        rmock.post(
            "http://baseurl/system-messages",
            json={"systemMessages": {
                'id': 123,
                'slug': 'test-system-message',
                'data': {
                    "system-message-key": "system-message-value"
                },
                'show': False,
            }},
            status_code=201,
        )

        result = data_client.create_system_message(
            'test-system-message',
            {
                "system-message-key": "system-message-value"
            },
            user="test@example.com"
        )

        assert result == {
            "systemMessages": {
                'id': 123,
                'slug': 'test-system-message',
                'data': {
                    "system-message-key": "system-message-value"
                },
                'show': False,
            }
        }
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "systemMessages": {
                'slug': 'test-system-message',
                'data': {
                    "system-message-key": "system-message-value"
                }
            }
        }

    @pytest.mark.parametrize('show', (False, True))
    def test_create_system_with_show(self, data_client, rmock, show):
        rmock.post(
            "http://baseurl/system-messages",
            json={"systemMessages": {
                'id': 123,
                'slug': 'test-system-message',
                'data': {
                    "system-message-key": "system-message-value"
                },
                'show': show,
            }},
            status_code=201,
        )

        result = data_client.create_system_message(
            'test-system-message',
            {
                "system-message-key": "system-message-value"
            },
            show=show,
            user="test@example.com"
        )

        assert result == {
            "systemMessages": {
                'id': 123,
                'slug': 'test-system-message',
                'data': {
                    "system-message-key": "system-message-value"
                },
                'show': show,
            }
        }
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "systemMessages": {
                'slug': 'test-system-message',
                'data': {
                    "system-message-key": "system-message-value"
                },
                'show': show
            }
        }

    def test_update_system_message_with_data(self, data_client, rmock):
        rmock.post(
            "http://baseurl/system-messages/test-system-message",
            json={"systemMessages": {
                'id': 123,
                'slug': 'test-system-message',
                'data': {
                    "system-message-key": "system-message-value"
                },
                'show': False,
            }},
            status_code=200,
        )

        result = data_client.update_system_message(
            'test-system-message',
            {
                "system-message-key": "system-message-value"
            },
            user="test@example.com"
        )

        assert result == {
            "systemMessages": {
                'id': 123,
                'slug': 'test-system-message',
                'data': {
                    "system-message-key": "system-message-value"
                },
                'show': False,
            }
        }
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "systemMessages": {
                'data': {
                    "system-message-key": "system-message-value"
                }
            }
        }

    @pytest.mark.parametrize('show', (False, True))
    def test_update_system_with_show(self, data_client, rmock, show):
        rmock.post(
            "http://baseurl/system-messages/test-system-message",
            json={"systemMessages": {
                'id': 123,
                'slug': 'test-system-message',
                'data': {
                    "system-message-key": "system-message-value"
                },
                'show': show,
            }},
            status_code=200,
        )

        result = data_client.update_system_message(
            'test-system-message',
            show=show,
            user="test@example.com"
        )

        assert result == {
            "systemMessages": {
                'id': 123,
                'slug': 'test-system-message',
                'data': {
                    "system-message-key": "system-message-value"
                },
                'show': show,
            }
        }
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "systemMessages": {
                'show': show
            }
        }

    def test_update_system_message_with_show_and_data(self, data_client, rmock):
        rmock.post(
            "http://baseurl/system-messages/test-system-message",
            json={"systemMessages": {
                'id': 123,
                'slug': 'test-system-message',
                'data': {
                    "system-message-key": "system-message-value"
                },
                'show': True,
            }},
            status_code=200,
        )

        result = data_client.update_system_message(
            'test-system-message',
            {
                "system-message-key": "system-message-value"
            },
            True,
            user="test@example.com"
        )

        assert result == {
            "systemMessages": {
                'id': 123,
                'slug': 'test-system-message',
                'data': {
                    "system-message-key": "system-message-value"
                },
                'show': True,
            }
        }
        assert rmock.called
        assert rmock.last_request.json() == {
            "updated_by": "test@example.com",
            "systemMessages": {
                'data': {
                    "system-message-key": "system-message-value"
                },
                'show': True,
            }
        }


class TestLotQuestionsResponsesMethods(object):
    def test_find_lot_questions_responses(self, data_client, rmock):
        rmock.get(
            "http://baseurl/lot-questions-responses?framework=g-cloud-6&supplier_id=1234",
            json={"lotQuestionsResponses": "result"},
            status_code=200)

        result = data_client.find_lot_questions_responses(1234, 'g-cloud-6')

        assert result == {"lotQuestionsResponses": "result"}
        assert rmock.called

    def test_find_lot_questions_responses_adds_page_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/lot-questions-responses?framework=g-cloud-6&supplier_id=1234&page=2",
            json={"lotQuestionsResponses": "result"},
            status_code=200)

        result = data_client.find_lot_questions_responses(1234, 'g-cloud-6', page=2)

        assert result == {"lotQuestionsResponses": "result"}
        assert rmock.called

    def test_find_lot_questions_responses_applicants_for_framework_lot(self, data_client, rmock):
        rmock.get(
            "http://baseurl/lot-questions-responses/applications?framework=g-cloud-6&lot=g-lot",
            json={"lotQuestionsResponses": "result"},
            status_code=200
        )

        result = data_client.find_lot_questions_responses_applicants_for_framework_lot('g-cloud-6', 'g-lot')

        assert result == {"lotQuestionsResponses": "result"}
        assert rmock.called

    def test_find_lot_questions_responses_applicants_for_framework_lot_adds_with_evaluations_parameter(
        self,
        data_client,
        rmock
    ):
        rmock.get(
            "http://baseurl/lot-questions-responses/applications?framework=g-cloud-6&lot=g-lot&with_evaluations=True",
            json={"lotQuestionsResponses": "result"},
            status_code=200
        )

        result = data_client.find_lot_questions_responses_applicants_for_framework_lot(
            'g-cloud-6',
            'g-lot',
            with_evaluations=True
        )

        assert result == {"lotQuestionsResponses": "result"}
        assert rmock.called

    def test_find_lot_questions_responses_applicants_for_framework_lot_adds_page_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/lot-questions-responses/applications?framework=g-cloud-6&lot=g-lot&page=2",
            json={"lotQuestionsResponses": "result"},
            status_code=200
        )

        result = data_client.find_lot_questions_responses_applicants_for_framework_lot('g-cloud-6', 'g-lot', page=2)

        assert result == {"lotQuestionsResponses": "result"}
        assert rmock.called

    def test_create_lot_questions_response(self, data_client, rmock):
        rmock.post(
            "http://baseurl/lot-questions-responses",
            json={"lotQuestionsResponses": {"question": "answer"}},
            status_code=201)

        result = data_client.create_lot_questions_response(1234, 'g-cloud-6', 'g-lot', "user")

        assert result == {'lotQuestionsResponses': {'question': 'answer'}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'supplierId': 1234,
            'frameworkSlug': 'g-cloud-6',
            'lotSlug': 'g-lot',
            'updated_by': 'user',
        }

    def test_get_lot_questions_response(self, data_client, rmock):
        rmock.get(
            "http://baseurl/lot-questions-responses/1234",
            json={"lotQuestionsResponses": "result"},
            status_code=200)

        result = data_client.get_lot_questions_response(1234)

        assert result == {"lotQuestionsResponses": "result"}
        assert rmock.called

    def test_get_lot_questions_response_should_return_404(self, data_client, rmock):
        rmock.get(
            "http://baseurl/lot-questions-responses/1234",
            status_code=404)

        try:
            data_client.get_lot_questions_response(1234)
        except HTTPError:
            assert rmock.called

    def test_get_lot_questions_response_with_evaluations(self, data_client, rmock):
        rmock.get(
            "http://baseurl/lot-questions-responses/1234?with_evaluations=True",
            json={"lotQuestionsResponses": "result"},
            status_code=200)

        result = data_client.get_lot_questions_response(1234, with_evaluations=True)

        assert result == {"lotQuestionsResponses": "result"}
        assert rmock.called

    def test_get_lot_questions_response_by_framework_lot_suppler(self, data_client, rmock):
        rmock.get(
            "http://baseurl/lot-questions-responses/frameworks/g-cloud-6/lots/g-things/suppliers/1234",
            json={"lotQuestionsResponses": "result"},
            status_code=200)

        result = data_client.get_lot_questions_response_by_framework_lot_suppler(
            'g-cloud-6',
            'g-things',
            1234
        )

        assert result == {"lotQuestionsResponses": "result"}
        assert rmock.called

    def test_get_lot_questions_response_by_framework_lot_suppler_should_return_404(self, data_client, rmock):
        rmock.get(
            "http://baseurl/lot-questions-responses/frameworks/g-cloud-6/lots/g-things/suppliers/1234",
            status_code=404)

        try:
            data_client.get_lot_questions_response_by_framework_lot_suppler(
                'g-cloud-6',
                'g-things',
                1234
            )
        except HTTPError:
            assert rmock.called

    def test_update_lot_questions_response(self, data_client, rmock):
        rmock.patch(
            "http://baseurl/lot-questions-responses/1234",
            json={"lotQuestionsResponses": {"question": "answer"}},
            status_code=200
        )

        result = data_client.update_lot_questions_response(1234, {"question": "answer"}, "user")

        assert result == {'lotQuestionsResponses': {'question': 'answer'}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
            'lotQuestionsResponses': {'question': 'answer'}
        }

    def test_update_lot_questions_response_with_page_questions(self, data_client, rmock):
        rmock.patch(
            "http://baseurl/lot-questions-responses/1234",
            json={"lotQuestionsResponses": {"question": "answer"}},
            status_code=200
        )

        result = data_client.update_lot_questions_response(
            1234,
            {"question": "answer"},
            "user",
            ["question"]
        )

        assert result == {'lotQuestionsResponses': {'question': 'answer'}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
            'lotQuestionsResponses': {'question': 'answer'},
            'page_questions': ['question']
        }

    def test_complete_lot_questions_response(self, data_client, rmock):
        rmock.post(
            "http://baseurl/lot-questions-responses/1234/complete",
            json={"message": "done"},
            status_code=200)

        result = data_client.complete_lot_questions_response(1234, "user")

        assert result == {'message': 'done'}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
        }

    def test_find_lot_questions_response_section_evaluations(self, data_client, rmock):
        rmock.get(
            "http://baseurl/lot-questions-response-section-evaluations?"
            "framework=g-cloud-6&lot=g-things",
            json={"lotQuestionsResponseSectionEvaluations": "result"},
            status_code=200)

        result = data_client.find_lot_questions_response_section_evaluations('g-cloud-6', 'g-things')

        assert result == {"lotQuestionsResponseSectionEvaluations": "result"}
        assert rmock.called

    def ttest_find_lot_questions_response_section_evaluations_adds_page_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/lot-questions-response-section-evaluations?"
            "framework=g-cloud-6&lot=g-things&page=2",
            json={"lotQuestionsResponseSectionEvaluations": "result"},
            status_code=200)

        result = data_client.find_lot_questions_response_section_evaluations('g-cloud-6', 'g-things', page=2)

        assert result == {"lotQuestionsResponseSectionEvaluations": "result"}
        assert rmock.called

    def test_find_lot_questions_response_section_evaluations_adds_section_slug_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/lot-questions-response-section-evaluations?"
            "framework=g-cloud-6&lot=g-things&section_slug=the-slug",
            json={"lotQuestionsResponseSectionEvaluations": "result"},
            status_code=200)

        result = data_client.find_lot_questions_response_section_evaluations(
            'g-cloud-6',
            'g-things',
            section_slug='the-slug'
        )

        assert result == {"lotQuestionsResponseSectionEvaluations": "result"}
        assert rmock.called

    def test_get_lot_questions_response_section_evaluation(self, data_client, rmock):
        rmock.get(
            "http://baseurl/lot-questions-response-section-evaluations/1234",
            json={"evaluatorFrameworkLotSectionEvaluations": "result"},
            status_code=200)

        result = data_client.get_lot_questions_response_section_evaluation(1234)

        assert result == {"evaluatorFrameworkLotSectionEvaluations": "result"}
        assert rmock.called

    def test_create_lot_questions_response_section_evaluation(self, data_client, rmock):
        rmock.post(
            "http://baseurl/lot-questions-response-section-evaluations",
            json={"message": "done"},
            status_code=200
        )

        result = data_client.create_lot_questions_response_section_evaluation(
            1234,
            'the-slug',
            {
                "comment": "This is the comment",
                "score": "50"
            },
            [
                "comment",
                "score"
            ],
            'user'
        )

        assert result == {'message': 'done'}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'lotQuestionsResponseId': 1234,
            'sectionSlug': 'the-slug',
            'lotQuestionsResponseSectionEvaluations': {
                "comment": "This is the comment",
                "score": "50"
            },
            'page_questions': [
                "comment",
                "score"
            ],
            'updated_by': 'user',
        }

    def test_update_lot_questions_response_section_evaluation(self, data_client, rmock):
        rmock.post(
            "http://baseurl/lot-questions-response-section-evaluations/1234",
            json={"message": "done"},
            status_code=200
        )

        result = data_client.update_lot_questions_response_section_evaluation(
            1234,
            {
                "comment": "This is the comment",
                "score": "50"
            },
            'user'
        )

        assert result == {'message': 'done'}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'lotQuestionsResponseSectionEvaluations': {
                "comment": "This is the comment",
                "score": "50"
            },
            'updated_by': 'user',
        }


class TestEvaluatorFrameworkLotMethods(object):
    def test_find_evaluator_framework_lots(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lots?assigned=True",
            json={"evaluatorFrameworkLots": "result"},
            status_code=200)

        result = data_client.find_evaluator_framework_lots()

        assert result == {"evaluatorFrameworkLots": "result"}
        assert rmock.called

    def test_find_evaluator_framework_lots_adds_framework_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lots?framework=g-cloud-6&assigned=True",
            json={"evaluatorFrameworkLots": "result"},
            status_code=200)

        result = data_client.find_evaluator_framework_lots('g-cloud-6')

        assert result == {"evaluatorFrameworkLots": "result"}
        assert rmock.called

    def test_find_evaluator_framework_lots_adds_lot_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lots?framework=g-cloud-6&lot=g-things&assigned=True",
            json={"evaluatorFrameworkLots": "result"},
            status_code=200)

        result = data_client.find_evaluator_framework_lots('g-cloud-6', 'g-things')

        assert result == {"evaluatorFrameworkLots": "result"}
        assert rmock.called

    def test_find_evaluator_framework_lots_adds_page_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lots?framework=g-cloud-6&lot=g-things&assigned=True&page=2",
            json={"evaluatorFrameworkLots": "result"},
            status_code=200)

        result = data_client.find_evaluator_framework_lots('g-cloud-6', 'g-things', page=2)

        assert result == {"evaluatorFrameworkLots": "result"}
        assert rmock.called

    def test_find_evaluator_framework_lots_adds_user_id_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lots?"
            "framework=g-cloud-6&lot=g-things&assigned=True&user_id=1",
            json={"evaluatorFrameworkLots": "result"},
            status_code=200)

        result = data_client.find_evaluator_framework_lots('g-cloud-6', 'g-things', user_id=1)

        assert result == {"evaluatorFrameworkLots": "result"}
        assert rmock.called

    def test_find_evaluator_framework_lots_adds_assigned_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lots?framework=g-cloud-6&lot=g-things&assigned=False",
            json={"evaluatorFrameworkLots": "result"},
            status_code=200)

        result = data_client.find_evaluator_framework_lots('g-cloud-6', 'g-things', assigned=False)

        assert result == {"evaluatorFrameworkLots": "result"}
        assert rmock.called

    def test_find_evaluator_framework_lot_adds_locked_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lots?"
            "framework=g-cloud-6&lot=g-things&assigned=True&locked=True",
            json={"evaluatorFrameworkLotSections": "result"},
            status_code=200)

        result = data_client.find_evaluator_framework_lots('g-cloud-6', 'g-things', locked=True)

        assert result == {"evaluatorFrameworkLotSections": "result"}
        assert rmock.called

    def test_find_evaluator_framework_lot_adds_with_sections_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lots?"
            "framework=g-cloud-6&lot=g-things&assigned=True&with_sections=True",
            json={"evaluatorFrameworkLotSections": "result"},
            status_code=200)

        result = data_client.find_evaluator_framework_lots('g-cloud-6', 'g-things', with_sections=True)

        assert result == {"evaluatorFrameworkLotSections": "result"}
        assert rmock.called

    def test_find_evaluator_framework_lot_adds_with_evaluations_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lots?"
            "framework=g-cloud-6&lot=g-things&assigned=True&with_evaluations=True",
            json={"evaluatorFrameworkLotSections": "result"},
            status_code=200)

        result = data_client.find_evaluator_framework_lots('g-cloud-6', 'g-things', with_evaluations=True)

        assert result == {"evaluatorFrameworkLotSections": "result"}
        assert rmock.called

    def test_get_evaluator_framework_lot(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lots/1234?with_sections=True&with_evaluations=True",
            json={"evaluatorFrameworkLots": "result"},
            status_code=200)

        result = data_client.get_evaluator_framework_lot(1234)

        assert result == {"evaluatorFrameworkLots": "result"}
        assert rmock.called

    def test_get_evaluator_framework_lot_adds_with_sections_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lots/1234?with_sections=False&with_evaluations=True",
            json={"evaluatorFrameworkLots": "result"},
            status_code=200)

        result = data_client.get_evaluator_framework_lot(1234, with_sections=False)

        assert result == {"evaluatorFrameworkLots": "result"}
        assert rmock.called

    def test_get_evaluator_framework_lot_adds_with_evaluations_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lots/1234?with_sections=True&with_evaluations=False",
            json={"evaluatorFrameworkLots": "result"},
            status_code=200)

        result = data_client.get_evaluator_framework_lot(1234, with_evaluations=False)

        assert result == {"evaluatorFrameworkLots": "result"}
        assert rmock.called

    def test_update_assigned_evaluators_for_framework_lot(self, data_client, rmock):
        rmock.post(
            "http://baseurl/evaluations/evaluator-framework-lots",
            json={"message": "done"},
            status_code=200
        )

        result = data_client.update_assigned_evaluators_for_framework_lot(
            'g-cloud-6',
            'g-lot',
            [
                123,
                456
            ],
            'user'
        )

        assert result == {'message': 'done'}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'evaluatorFrameworkLots': {
                'frameworkSlug': 'g-cloud-6',
                'lotSlug': 'g-lot',
                'users': [
                    123,
                    456
                ],
            },
            'updated_by': 'user',
        }

    def test_update_evaluator_framework_lot_status(self, data_client, rmock):
        rmock.post(
            "http://baseurl/evaluations/evaluator-framework-lots/1234/status/locked",
            json={"message": "done"},
            status_code=200
        )

        result = data_client.update_evaluator_framework_lot_status(
            1234,
            'locked',
            'user'
        )

        assert result == {'message': 'done'}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
        }

    def test_find_evaluator_framework_lot_sections(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lot-sections?"
            "framework=g-cloud-6&lot=g-things&assigned=True",
            json={"evaluatorFrameworkLotSections": "result"},
            status_code=200)

        result = data_client.find_evaluator_framework_lot_sections('g-cloud-6', 'g-things')

        assert result == {"evaluatorFrameworkLotSections": "result"}
        assert rmock.called

    def test_find_evaluator_framework_lot_sections_adds_page_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lot-sections?"
            "framework=g-cloud-6&lot=g-things&assigned=True&page=2",
            json={"evaluatorFrameworkLotSections": "result"},
            status_code=200)

        result = data_client.find_evaluator_framework_lot_sections('g-cloud-6', 'g-things', page=2)

        assert result == {"evaluatorFrameworkLotSections": "result"}
        assert rmock.called

    def test_find_evaluator_framework_lot_sections_adds_section_slug_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lot-sections?"
            "framework=g-cloud-6&lot=g-things&assigned=True&section_slug=the-slug",
            json={"evaluatorFrameworkLotSections": "result"},
            status_code=200)

        result = data_client.find_evaluator_framework_lot_sections('g-cloud-6', 'g-things', section_slug='the-slug')

        assert result == {"evaluatorFrameworkLotSections": "result"}
        assert rmock.called

    def test_find_evaluator_framework_lot_sections_adds_assigned_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lot-sections?"
            "framework=g-cloud-6&lot=g-things&assigned=False",
            json={"evaluatorFrameworkLotSections": "result"},
            status_code=200)

        result = data_client.find_evaluator_framework_lot_sections('g-cloud-6', 'g-things', assigned=False)

        assert result == {"evaluatorFrameworkLotSections": "result"}
        assert rmock.called

    def test_find_evaluator_framework_lot_sections_adds_locked_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lot-sections?"
            "framework=g-cloud-6&lot=g-things&assigned=True&locked=True",
            json={"evaluatorFrameworkLotSections": "result"},
            status_code=200)

        result = data_client.find_evaluator_framework_lot_sections('g-cloud-6', 'g-things', locked=True)

        assert result == {"evaluatorFrameworkLotSections": "result"}
        assert rmock.called

    def test_find_evaluator_framework_lot_sections_adds_with_evaluations_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lot-sections?"
            "framework=g-cloud-6&lot=g-things&assigned=True&with_evaluations=True",
            json={"evaluatorFrameworkLotSections": "result"},
            status_code=200)

        result = data_client.find_evaluator_framework_lot_sections('g-cloud-6', 'g-things', with_evaluations=True)

        assert result == {"evaluatorFrameworkLotSections": "result"}
        assert rmock.called

    def test_update_assigned_sections_for_evaluator_framework_lot(self, data_client, rmock):
        rmock.post(
            "http://baseurl/evaluations/evaluator-framework-lot-sections",
            json={"message": "done"},
            status_code=200
        )

        result = data_client.update_assigned_sections_for_evaluator_framework_lot(
            'g-cloud-6',
            'g-lot',
            'section-slug',
            [
                123,
                456
            ],
            'user'
        )

        assert result == {'message': 'done'}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'evaluatorFrameworkLotSections': {
                'evaluatorFrameworkLots': [
                    123,
                    456
                ],
                'frameworkSlug': 'g-cloud-6',
                'lotSlug': 'g-lot',
                'sectionSlug': 'section-slug',
            },
            'updated_by': 'user',
        }

    def test_get_evaluator_framework_lot_section(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lot-sections/1234?with_evaluations=True",
            json={"evaluatorFrameworkLotSections": "result"},
            status_code=200)

        result = data_client.get_evaluator_framework_lot_section(1234)

        assert result == {"evaluatorFrameworkLotSections": "result"}
        assert rmock.called

    def test_get_evaluator_framework_lot_section_adds_with_evaluations_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lot-sections/1234?with_evaluations=False",
            json={"evaluatorFrameworkLotSections": "result"},
            status_code=200)

        result = data_client.get_evaluator_framework_lot_section(1234, with_evaluations=False)

        assert result == {"evaluatorFrameworkLotSections": "result"}
        assert rmock.called

    def test_find_evaluator_framework_lot_section_evaluations(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lot-section-evaluations?"
            "framework=g-cloud-6&lot=g-things",
            json={"evaluatorFrameworkLotSectionEvaluations": "result"},
            status_code=200)

        result = data_client.find_evaluator_framework_lot_section_evaluations('g-cloud-6', 'g-things')

        assert result == {"evaluatorFrameworkLotSectionEvaluations": "result"}
        assert rmock.called

    def test_find_evaluator_framework_lot_section_evaluations_adds_page_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lot-section-evaluations?"
            "framework=g-cloud-6&lot=g-things&page=2",
            json={"evaluatorFrameworkLotSectionEvaluations": "result"},
            status_code=200)

        result = data_client.find_evaluator_framework_lot_section_evaluations('g-cloud-6', 'g-things', page=2)

        assert result == {"evaluatorFrameworkLotSectionEvaluations": "result"}
        assert rmock.called

    def test_find_evaluator_framework_lot_section_evaluations_adds_section_slug_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lot-section-evaluations?"
            "framework=g-cloud-6&lot=g-things&section_slug=the-slug",
            json={"evaluatorFrameworkLotSectionEvaluations": "result"},
            status_code=200)

        result = data_client.find_evaluator_framework_lot_section_evaluations(
            'g-cloud-6',
            'g-things',
            section_slug='the-slug'
        )

        assert result == {"evaluatorFrameworkLotSectionEvaluations": "result"}
        assert rmock.called

    def test_find_evaluator_framework_lot_section_evaluations_adds_evaluator_framework_lot_id_parameter(
        self,
        data_client,
        rmock
    ):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lot-section-evaluations?"
            "framework=g-cloud-6&lot=g-things&evaluator_framework_lot_id=1234",
            json={"evaluatorFrameworkLotSectionEvaluations": "result"},
            status_code=200)

        result = data_client.find_evaluator_framework_lot_section_evaluations(
            'g-cloud-6',
            'g-things',
            evaluator_framework_lot_id=1234
        )

        assert result == {"evaluatorFrameworkLotSectionEvaluations": "result"}
        assert rmock.called

    def test_find_evaluator_framework_lot_section_evaluations_adds_supplier_id_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lot-section-evaluations?"
            "framework=g-cloud-6&lot=g-things&supplier_id=123",
            json={"evaluatorFrameworkLotSectionEvaluations": "result"},
            status_code=200)

        result = data_client.find_evaluator_framework_lot_section_evaluations('g-cloud-6', 'g-things', supplier_id=123)

        assert result == {"evaluatorFrameworkLotSectionEvaluations": "result"}
        assert rmock.called

    def test_create_evaluator_framework_lot_section_evaluation(self, data_client, rmock):
        rmock.post(
            "http://baseurl/evaluations/evaluator-framework-lot-section-evaluations",
            json={"message": "done"},
            status_code=200
        )

        result = data_client.create_evaluator_framework_lot_section_evaluation(
            1234,
            5678,
            {
                "comment": "This is the comment",
                "score": "50"
            },
            [
                "comment",
                "score"
            ],
            'user'
        )

        assert result == {'message': 'done'}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'evaluatorFrameworkLotSectionId': 1234,
            'supplierId': 5678,
            'evaluatorFrameworkLotSectionEvaluations': {
                "comment": "This is the comment",
                "score": "50"
            },
            'page_questions': [
                "comment",
                "score"
            ],
            'updated_by': 'user',
        }

    def test_get_evaluator_framework_lot_section_evaluation(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lot-section-evaluations/1234",
            json={"evaluatorFrameworkLotSectionEvaluations": "result"},
            status_code=200)

        result = data_client.get_evaluator_framework_lot_section_evaluation(1234)

        assert result == {"evaluatorFrameworkLotSectionEvaluations": "result"}
        assert rmock.called

    def test_get_evaluator_framework_lot_section_evaluation_with_lot_questions_response(self, data_client, rmock):
        rmock.get(
            "http://baseurl/evaluations/evaluator-framework-lot-section-evaluations/1234"
            "?with_lot_questions_response=True",
            json={"evaluatorFrameworkLotSectionEvaluations": "result"},
            status_code=200)

        result = data_client.get_evaluator_framework_lot_section_evaluation(1234, with_lot_questions_response=True)

        assert result == {"evaluatorFrameworkLotSectionEvaluations": "result"}
        assert rmock.called

    def test_update_evaluator_framework_lot_section_evaluation(self, data_client, rmock):
        rmock.post(
            "http://baseurl/evaluations/evaluator-framework-lot-section-evaluations/1234",
            json={"message": "done"},
            status_code=200
        )

        result = data_client.update_evaluator_framework_lot_section_evaluation(
            1234,
            {
                "comment": "This is the comment",
                "score": "50"
            },
            'user'
        )

        assert result == {'message': 'done'}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'evaluatorFrameworkLotSectionEvaluations': {
                "comment": "This is the comment",
                "score": "50"
            },
            'updated_by': 'user',
        }


class TestTechnicalAbilityCertificatesMethods(object):
    def test_find_technical_ability_certificates(self, data_client, rmock):
        rmock.get(
            "http://baseurl/technical-ability-certificates?framework=g-cloud-6&supplier_id=1234",
            json={"technicalAbilityCertificates": "result"},
            status_code=200)

        result = data_client.find_technical_ability_certificates(1234, 'g-cloud-6')

        assert result == {"technicalAbilityCertificates": "result"}
        assert rmock.called

    def test_find_technical_ability_certificates_adds_page_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/technical-ability-certificates?framework=g-cloud-6&supplier_id=1234&page=2",
            json={"technicalAbilityCertificates": "result"},
            status_code=200)

        result = data_client.find_technical_ability_certificates(1234, 'g-cloud-6', page=2)

        assert result == {"technicalAbilityCertificates": "result"}
        assert rmock.called

    def test_create_technical_ability_certificates(self, data_client, rmock):
        rmock.post(
            "http://baseurl/technical-ability-certificates",
            json={"technicalAbilityCertificates": {"question": "answer"}},
            status_code=201)

        result = data_client.create_technical_ability_certificate(1234, 'g-cloud-6', 'g-lot', "user")

        assert result == {'technicalAbilityCertificates': {'question': 'answer'}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'supplierId': 1234,
            'frameworkSlug': 'g-cloud-6',
            'lotSlug': 'g-lot',
            'updated_by': 'user',
        }

    def test_get_technical_ability_certificate(self, data_client, rmock):
        rmock.get(
            "http://baseurl/technical-ability-certificates/1234",
            json={"tac": "data"},
            status_code=200
        )

        result = data_client.get_technical_ability_certificate(1234)

        assert result == {"tac": "data"}
        assert rmock.called

    def test_authenticate_technical_ability_certificate(self, data_client, rmock):
        rmock.post(
            "http://baseurl/technical-ability-certificates/auth",
            json={"authorization": True},
            status_code=200
        )

        result = data_client.authenticate_technical_ability_certificate("1234", "123456", "user")

        assert result == {"authorization": True}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
            'authTechnicalAbilityCertificates': {
                'authenticationId': "1234",
                'passcode': "123456",
            }
        }

    def verify_technical_ability_certificate_can_be_signed(self, data_client, rmock):
        rmock.post(
            "http://baseurl/technical-ability-certificates/verify-can-be-signed",
            json={"signable": True},
            status_code=200
        )

        result = data_client.verify_technical_ability_certificate_can_be_signed("1234")

        assert result == {"signable": True}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'verifyTechnicalAbilityCertificates': {
                'authenticationId': "1234",
            }
        }

    def test_update_technical_ability_certificate(self, data_client, rmock):
        rmock.patch(
            "http://baseurl/technical-ability-certificates/1234",
            json={"technicalAbilityCertificates": {"question": "answer"}},
            status_code=200
        )

        result = data_client.update_technical_ability_certificate(1234, {"question": "answer"}, "user")

        assert result == {'technicalAbilityCertificates': {'question': 'answer'}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
            'technicalAbilityCertificates': {'question': 'answer'}
        }

    def test_update_technical_ability_certificate_with_page_questions(self, data_client, rmock):
        rmock.patch(
            "http://baseurl/technical-ability-certificates/1234",
            json={"technicalAbilityCertificates": {"question": "answer"}},
            status_code=200
        )

        result = data_client.update_technical_ability_certificate(
            1234,
            {"question": "answer"},
            "user",
            ["question"]
        )

        assert result == {'technicalAbilityCertificates': {'question': 'answer'}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
            'technicalAbilityCertificates': {'question': 'answer'},
            'page_questions': ['question']
        }

    def test_send_technical_ability_certificate(self, data_client, rmock):
        rmock.post(
            "http://baseurl/technical-ability-certificates/1234/send",
            json={"message": "done", "authenticationId": "random-value", "passcode": "123456"},
            status_code=200
        )

        result = data_client.send_technical_ability_certificate(1234, "user")

        assert result == {"message": "done", "authenticationId": "random-value", "passcode": "123456"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
        }

    def test_revert_technical_ability_certificate_to_in_progress(self, data_client, rmock):
        rmock.post(
            "http://baseurl/technical-ability-certificates/1234/revert-to-in-progress",
            json={"message": "done"},
            status_code=200
        )

        result = data_client.revert_technical_ability_certificate_to_in_progress(1234, "user")

        assert result == {"message": "done"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
        }

    def test_approve_technical_ability_certificate(self, data_client, rmock):
        rmock.post(
            "http://baseurl/technical-ability-certificates/1234/approve",
            json={"message": "done"},
            status_code=200
        )

        result = data_client.approve_technical_ability_certificate(1234, "Elma", "user")

        assert result == {"message": "done"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
            'electronicSignature': "Elma"
        }


class TestLotPricingsMethods(object):
    def test_find_lot_pricings(self, data_client, rmock):
        rmock.get(
            "http://baseurl/lot-pricings?framework=g-cloud-6&supplier_id=1234",
            json={"lotPricings": "result"},
            status_code=200)

        result = data_client.find_lot_pricings(1234, 'g-cloud-6')

        assert result == {"lotPricings": "result"}
        assert rmock.called

    def test_find_lot_pricings_adds_page_parameter(self, data_client, rmock):
        rmock.get(
            "http://baseurl/lot-pricings?framework=g-cloud-6&supplier_id=1234&page=2",
            json={"lotPricings": "result"},
            status_code=200)

        result = data_client.find_lot_pricings(1234, 'g-cloud-6', page=2)

        assert result == {"lotPricings": "result"}
        assert rmock.called

    def test_create_lot_pricing(self, data_client, rmock):
        rmock.post(
            "http://baseurl/lot-pricings",
            json={"lotPricings": {"question": "answer"}},
            status_code=201)

        result = data_client.create_lot_pricing(1234, 'g-cloud-6', 'g-lot', "user")

        assert result == {'lotPricings': {'question': 'answer'}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'supplierId': 1234,
            'frameworkSlug': 'g-cloud-6',
            'lotSlug': 'g-lot',
            'updated_by': 'user',
        }

    def test_get_lot_pricing(self, data_client, rmock):
        rmock.get(
            "http://baseurl/lot-pricings/1234",
            json={"lotPricings": "result"},
            status_code=200)

        result = data_client.get_lot_pricing(1234)

        assert result == {"lotPricings": "result"}
        assert rmock.called

    def test_get_lot_pricing_should_return_404(self, data_client, rmock):
        rmock.get(
            "http://baseurl/lot-pricings/1234",
            status_code=404)

        try:
            data_client.get_lot_pricing(1234)
        except HTTPError:
            assert rmock.called

    def test_update_lot_pricing(self, data_client, rmock):
        rmock.patch(
            "http://baseurl/lot-pricings/1234",
            json={"lotPricings": {"question": "answer"}},
            status_code=200
        )

        result = data_client.update_lot_pricing(1234, {"question": "answer"}, "user")

        assert result == {'lotPricings': {'question': 'answer'}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
            'lotPricings': {'question': 'answer'}
        }

    def test_update_lot_pricing_with_page_questions(self, data_client, rmock):
        rmock.patch(
            "http://baseurl/lot-pricings/1234",
            json={"lotPricings": {"question": "answer"}},
            status_code=200
        )

        result = data_client.update_lot_pricing(
            1234,
            {"question": "answer"},
            "user",
            ["question"]
        )

        assert result == {'lotPricings': {'question': 'answer'}}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
            'lotPricings': {'question': 'answer'},
            'page_questions': ['question']
        }

    def test_complete_lot_pricing(self, data_client, rmock):
        rmock.post(
            "http://baseurl/lot-pricings/1234/complete",
            json={"message": "done"},
            status_code=200)

        result = data_client.complete_lot_pricing(1234, "user")

        assert result == {'message': 'done'}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
        }
