from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse
from django.test.client import RequestFactory

from kitsune.access.decorators import login_required, logout_required, permission_required
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import UserFactory


def simple_view(request):
    return HttpResponse()


class LogoutRequiredTestCase(TestCase):
    def test_logged_out_default(self):
        request = RequestFactory().get("/foo")
        request.user = AnonymousUser()
        view = logout_required(simple_view)
        response = view(request)
        self.assertEqual(200, response.status_code)

    def test_logged_in_default(self):
        request = RequestFactory().get("/foo")
        request.user = UserFactory()
        view = logout_required(simple_view)
        response = view(request)
        self.assertEqual(302, response.status_code)

    def test_logged_in_argument(self):
        request = RequestFactory().get("/foo")
        request.user = UserFactory()
        view = logout_required("/bar")(simple_view)
        response = view(request)
        self.assertEqual(302, response.status_code)
        self.assertEqual("/bar", response["location"])

    def test_no_redirect_ajax(self):
        """Ajax requests should not redirect."""
        request = RequestFactory().get("/foo")
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"
        request.user = UserFactory()
        view = logout_required(simple_view)
        response = view(request)
        self.assertEqual(403, response.status_code)


class LoginRequiredTestCase(TestCase):
    def test_logged_out_default(self):
        request = RequestFactory().get("/foo")
        request.user = AnonymousUser()
        view = login_required(simple_view)
        response = view(request)
        self.assertEqual(302, response.status_code)

    def test_logged_in_default(self):
        """Active user login."""
        request = RequestFactory().get("/foo")
        request.user = UserFactory()
        view = login_required(simple_view)
        response = view(request)
        self.assertEqual(200, response.status_code)

    def test_logged_in_inactive(self):
        """Inactive user login not allowed by default."""
        request = RequestFactory().get("/foo")
        request.user = UserFactory(is_active=False)
        view = login_required(simple_view)
        response = view(request)
        self.assertEqual(302, response.status_code)

    def test_logged_in_inactive_allow(self):
        """Inactive user login explicitly allowed."""
        request = RequestFactory().get("/foo")
        request.user = UserFactory(is_active=False)
        view = login_required(simple_view, only_active=False)
        response = view(request)
        self.assertEqual(200, response.status_code)

    def test_no_redirect_ajax(self):
        """Ajax requests should not redirect."""
        request = RequestFactory().get("/foo")
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"
        request.user = AnonymousUser()
        view = login_required(simple_view)
        response = view(request)
        self.assertEqual(403, response.status_code)


class PermissionRequiredTestCase(TestCase):
    def test_logged_out_default(self):
        request = RequestFactory().get("/foo")
        request.user = AnonymousUser()
        view = permission_required("perm")(simple_view)
        response = view(request)
        self.assertEqual(302, response.status_code)

    def test_logged_in_default(self):
        request = RequestFactory().get("/foo")
        request.user = UserFactory()
        view = permission_required("perm")(simple_view)
        response = view(request)
        self.assertEqual(403, response.status_code)

    def test_logged_in_inactive(self):
        """Inactive user is denied access."""
        request = RequestFactory().get("/foo")
        request.user = UserFactory(is_active=False)
        view = permission_required("perm")(simple_view)
        response = view(request)
        self.assertEqual(403, response.status_code)

    def test_logged_in_admin(self):
        request = RequestFactory().get("/foo")
        request.user = UserFactory(is_staff=True, is_superuser=True)
        view = permission_required("perm")(simple_view)
        response = view(request)
        self.assertEqual(200, response.status_code)

    def test_no_redirect_ajax(self):
        """Ajax requests should not redirect."""
        request = RequestFactory().get("/foo")
        request.META["HTTP_X_REQUESTED_WITH"] = "XMLHttpRequest"
        request.user = AnonymousUser()
        view = permission_required("perm")(simple_view)
        response = view(request)
        self.assertEqual(403, response.status_code)
