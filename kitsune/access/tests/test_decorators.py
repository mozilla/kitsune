from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponse

import test_utils
from nose.tools import eq_

from kitsune.access.decorators import (
    logout_required, login_required, permission_required)
from kitsune.sumo.tests import TestCase
from kitsune.users.tests import user


def simple_view(request):
    return HttpResponse()


class LogoutRequiredTestCase(TestCase):
    def test_logged_out_default(self):
        request = test_utils.RequestFactory().get('/foo')
        request.user = AnonymousUser()
        view = logout_required(simple_view)
        response = view(request)
        eq_(200, response.status_code)

    def test_logged_in_default(self):
        request = test_utils.RequestFactory().get('/foo')
        request.user = user(save=True)
        view = logout_required(simple_view)
        response = view(request)
        eq_(302, response.status_code)

    def test_logged_in_argument(self):
        request = test_utils.RequestFactory().get('/foo')
        request.user = user(save=True)
        view = logout_required('/bar')(simple_view)
        response = view(request)
        eq_(302, response.status_code)
        eq_('/bar', response['location'])

    def test_no_redirect_ajax(self):
        """Ajax requests should not redirect."""
        request = test_utils.RequestFactory().get('/foo')
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request.user = user(save=True)
        view = logout_required(simple_view)
        response = view(request)
        eq_(403, response.status_code)


class LoginRequiredTestCase(TestCase):
    def test_logged_out_default(self):
        request = test_utils.RequestFactory().get('/foo')
        request.user = AnonymousUser()
        view = login_required(simple_view)
        response = view(request)
        eq_(302, response.status_code)

    def test_logged_in_default(self):
        """Active user login."""
        request = test_utils.RequestFactory().get('/foo')
        request.user = user(save=True)
        view = login_required(simple_view)
        response = view(request)
        eq_(200, response.status_code)

    def test_logged_in_inactive(self):
        """Inactive user login not allowed by default."""
        request = test_utils.RequestFactory().get('/foo')
        request.user = user(is_active=False, save=True)
        view = login_required(simple_view)
        response = view(request)
        eq_(302, response.status_code)

    def test_logged_in_inactive_allow(self):
        """Inactive user login explicitly allowed."""
        request = test_utils.RequestFactory().get('/foo')
        request.user = user(is_active=False, save=True)
        view = login_required(simple_view, only_active=False)
        response = view(request)
        eq_(200, response.status_code)

    def test_no_redirect_ajax(self):
        """Ajax requests should not redirect."""
        request = test_utils.RequestFactory().get('/foo')
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request.user = AnonymousUser()
        view = login_required(simple_view)
        response = view(request)
        eq_(403, response.status_code)


class PermissionRequiredTestCase(TestCase):
    def test_logged_out_default(self):
        request = test_utils.RequestFactory().get('/foo')
        request.user = AnonymousUser()
        view = permission_required('perm')(simple_view)
        response = view(request)
        eq_(302, response.status_code)

    def test_logged_in_default(self):
        request = test_utils.RequestFactory().get('/foo')
        request.user = user(save=True)
        view = permission_required('perm')(simple_view)
        response = view(request)
        eq_(403, response.status_code)

    def test_logged_in_inactive(self):
        """Inactive user is denied access."""
        request = test_utils.RequestFactory().get('/foo')
        request.user = user(is_active=False, save=True)
        view = permission_required('perm')(simple_view)
        response = view(request)
        eq_(403, response.status_code)

    def test_logged_in_admin(self):
        request = test_utils.RequestFactory().get('/foo')
        request.user = user(is_staff=True, is_superuser=True, save=True)
        view = permission_required('perm')(simple_view)
        response = view(request)
        eq_(200, response.status_code)

    def test_no_redirect_ajax(self):
        """Ajax requests should not redirect."""
        request = test_utils.RequestFactory().get('/foo')
        request.META['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        request.user = AnonymousUser()
        view = permission_required('perm')(simple_view)
        response = view(request)
        eq_(403, response.status_code)
