from .base import BaseAPIClient
from .errors import APIError


class TasksAPIClient(BaseAPIClient):
    def init_app(self, app):
        self._base_url = app.config['DM_TASKS_API_URL']
        self._auth_token = app.config['DM_TASKS_API_AUTH_TOKEN']

    # Worker status

    def get_worker_status(self):
        try:
            return self._get(f"{self._base_url}/_worker-status")
        except APIError as e:
            try:
                return e.response.json()
            except (ValueError, AttributeError):
                return {
                    "status": "error",
                    "workers": {},
                    "message": f"{e.message}",
                }

    # Notifications

    def notify_suppliers_of_framework_application_event(
        self,
        framework_slug,
        notification_template_name=None,
        notification_template_id=None,
        user=None
    ):
        return self._post_with_updated_by(
            f"/frameworks/{framework_slug}/notifications/framework-application-event",
            data={
                "notificationTemplateName": notification_template_name,
                "notificationTemplateId": notification_template_id,
            },
            user=user,
        )
