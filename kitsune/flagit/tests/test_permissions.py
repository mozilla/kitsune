from kitsune.flagit.models import FlaggedObject
from kitsune.flagit.tests import TestCaseBase
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory, add_permission


class FlagitTestPermissions(TestCaseBase):
    """Test our new permission required decorator."""

    def setUp(self):
        super(FlagitTestPermissions, self).setUp()
        self.user = UserFactory()

    def test_permission_required(self):
        url = reverse("flagit.queue", force_locale=True)
        resp = self.client.get(url)
        self.assertEqual(302, resp.status_code)

        self.client.login(username=self.user.username, password="testpass")
        resp = self.client.get(url)
        self.assertEqual(403, resp.status_code)

        add_permission(self.user, FlaggedObject, "can_moderate")
        resp = self.client.get(url)
        self.assertEqual(200, resp.status_code)
