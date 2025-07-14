import pytest
from unittest import mock

from dmapiclient import TasksAPIClient


@pytest.fixture
def tasks_client():
    return TasksAPIClient('http://baseurl', 'auth-token', True)


class TestTaskApiClient(object):
    def test_init_app_sets_attributes(self, tasks_client):
        app = mock.Mock()
        app.config = {
            "DM_TASKS_API_URL": "http://example",
            "DM_TASKS_API_AUTH_TOKEN": "example-token",
        }
        tasks_client.init_app(app)

        assert tasks_client.base_url == "http://example"
        assert tasks_client.auth_token == "example-token"

    def test_get_status(self, tasks_client, rmock):
        rmock.get(
            "http://baseurl/_status",
            json={"status": "ok"},
            status_code=200)

        result = tasks_client.get_status()

        assert result['status'] == "ok"
        assert rmock.called

    def test_get_wroker_status(self, tasks_client, rmock):
        rmock.get(
            "http://baseurl/_worker-status",
            json={"status": "ok"},
            status_code=200)

        result = tasks_client.get_worker_status()

        assert result['status'] == "ok"
        assert rmock.called

    def test_updated_by_user_can_be_set_in_constructor(self, rmock):
        tasks_client = TasksAPIClient('http://baseurl', 'auth-token', user="testuser@example.com", enabled=True)

        rmock.post(
            "http://baseurl/frameworks/g-cloud-7/notifications/framework-application-event",
            json={"request_id": "999"},
            status_code=200
        )

        tasks_client.notify_suppliers_of_framework_application_event('g-cloud-7')

        assert rmock.request_history[0].json() == {
            'updated_by': 'testuser@example.com',
            'notificationTemplateName': None,
            'notificationTemplateId': None,
        }

    def test_value_error_is_raised_if_no_user_in_constructor_or_method_call(self, tasks_client, rmock):
        rmock.post(
            "http://baseurl/frameworks/g-cloud-7/notifications/framework-application-event",
            json={"request_id": "999"},
            status_code=200
        )

        with pytest.raises(ValueError):
            tasks_client.notify_suppliers_of_framework_application_event('g-cloud-7')


class TestNotificationsMethods(object):
    def test_notify_suppliers_of_framework_application_event(self, tasks_client, rmock):
        rmock.post(
            "http://baseurl/frameworks/g-cloud-7/notifications/framework-application-event",
            json={"request_id": "999"},
            status_code=200,
        )

        result = tasks_client.notify_suppliers_of_framework_application_event('g-cloud-7', user='user')

        assert result == {"request_id": "999"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
            'notificationTemplateName': None,
            'notificationTemplateId': None,
        }

    @pytest.mark.parametrize(
        ('notification_template_name', 'notification_template_id'),
        (
            ("name", None),
            (None, "id"),
            ("name", "id")
        )
    )
    def test_notify_suppliers_of_framework_application_event_with_other_params(
        self,
        tasks_client,
        rmock,
        notification_template_name,
        notification_template_id
    ):
        rmock.post(
            "http://baseurl/frameworks/g-cloud-7/notifications/framework-application-event",
            json={"request_id": "999"},
            status_code=200,
        )

        result = tasks_client.notify_suppliers_of_framework_application_event(
            'g-cloud-7',
            user='user',
            notification_template_name=notification_template_name,
            notification_template_id=notification_template_id
        )

        assert result == {"request_id": "999"}
        assert rmock.called
        assert rmock.request_history[0].json() == {
            'updated_by': 'user',
            'notificationTemplateName': notification_template_name,
            'notificationTemplateId': notification_template_id,
        }
