from copy import copy
import hashlib
import os
from smtplib import SMTPRecipientsRefused

from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.core import mail
from django.core.files import File
from django.utils.http import int_to_base36

import mock
from nose.tools import eq_
from pyquery import PyQuery as pq

from flagit.models import FlaggedObject
from sumo.urlresolvers import reverse
from sumo.helpers import urlparams
from sumo.tests import post, get
from users import ERROR_SEND_EMAIL
from users.models import Profile, RegistrationProfile, RegistrationManager
from users.tests import TestCaseBase, user, add_permission, profile
from wiki.tests import revision


class LoginTests(TestCaseBase):
    """Login tests."""
    fixtures = ['users.json']

    def setUp(self):
        super(LoginTests, self).setUp()
        self.orig_debug = settings.DEBUG
        settings.DEBUG = True

    def tearDown(self):
        super(LoginTests, self).tearDown()
        settings.DEBUG = self.orig_debug

    def test_login_bad_password(self):
        '''Test login with a good username and bad password.'''
        response = post(self.client, 'users.login',
                        {'username': 'rrosario', 'password': 'foobar'})
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('Please enter a correct username and password. Note that both '
            'fields are case-sensitive.', doc('ul.errorlist li').text())

    def test_login_bad_username(self):
        '''Test login with a bad username.'''
        response = post(self.client, 'users.login',
                        {'username': 'foobarbizbin', 'password': 'testpass'})
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_('Please enter a correct username and password. Note that both '
            'fields are case-sensitive.', doc('ul.errorlist li').text())

    def test_login(self):
        '''Test a valid login.'''
        response = self.client.post(reverse('users.login'),
                                    {'username': 'rrosario',
                                     'password': 'testpass'})
        eq_(302, response.status_code)
        eq_('http://testserver' +
                reverse('home', locale=settings.LANGUAGE_CODE),
            response['location'])

    def test_login_next_parameter(self):
        '''Test with a valid ?next=url parameter.'''
        next = '/kb/new'

        # Verify that next parameter is set in form hidden field.
        response = self.client.get(urlparams(reverse('users.login'), next=next),
            follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(next, doc('input[name="next"]')[0].attrib['value'])

        # Verify that it gets used on form POST.
        response = self.client.post(reverse('users.login'),
                                    {'username': 'rrosario',
                                     'password': 'testpass',
                                     'next': next})
        eq_(302, response.status_code)
        eq_('http://testserver' + next, response['location'])

    @mock.patch.object(Site.objects, 'get_current')
    def test_login_invalid_next_parameter(self, get_current):
        '''Test with an invalid ?next=http://example.com parameter.'''
        get_current.return_value.domain = 'testserver.com'
        invalid_next = 'http://foobar.com/evil/'
        valid_next = reverse('home', locale=settings.LANGUAGE_CODE)

        # Verify that _valid_ next parameter is set in form hidden field.
        url = urlparams(reverse('users.login'), next=invalid_next)
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(valid_next, doc('input[name="next"]')[0].attrib['value'])

        # Verify that it gets used on form POST.
        response = self.client.post(reverse('users.login'),
                                    {'username': 'rrosario',
                                     'password': 'testpass',
                                     'next': invalid_next})
        eq_(302, response.status_code)
        eq_('http://testserver' + valid_next, response['location'])

    def test_login_legacy_password(self):
        '''Test logging in with a legacy md5 password.'''
        legacypw = 'legacypass'

        # Set the user's password to an md5
        u = User.objects.get(username='rrosario')
        u.password = hashlib.md5(legacypw).hexdigest()
        u.save()

        # Log in and verify that it's updated to a SHA-256
        response = self.client.post(reverse('users.login'),
                                    {'username': 'rrosario',
                                     'password': legacypw})
        eq_(302, response.status_code)
        u = User.objects.get(username='rrosario')
        assert u.password.startswith('sha256$')

        # Try to log in again.
        response = self.client.post(reverse('users.login'),
                                    {'username': 'rrosario',
                                     'password': legacypw})
        eq_(302, response.status_code)


class PasswordResetTests(TestCaseBase):
    fixtures = ['users.json']

    def setUp(self):
        super(PasswordResetTests, self).setUp()
        self.user = User.objects.get(username='rrosario')
        self.user.email = 'valid@email.com'
        self.user.save()
        self.uidb36 = int_to_base36(self.user.id)
        self.token = default_token_generator.make_token(self.user)
        self.orig_debug = settings.DEBUG
        settings.DEBUG = True

    def tearDown(self):
        super(PasswordResetTests, self).tearDown()
        settings.DEBUG = self.orig_debug

    def test_bad_email(self):
        r = self.client.post(reverse('users.pw_reset'),
                             {'email': 'foo@bar.com'})
        eq_(302, r.status_code)
        eq_('http://testserver/en-US/users/pwresetsent', r['location'])
        eq_(0, len(mail.outbox))

    @mock.patch.object(Site.objects, 'get_current')
    def test_success(self, get_current):
        get_current.return_value.domain = 'testserver.com'
        r = self.client.post(reverse('users.pw_reset'),
                             {'email': self.user.email})
        eq_(302, r.status_code)
        eq_('http://testserver/en-US/users/pwresetsent', r['location'])
        eq_(1, len(mail.outbox))
        assert mail.outbox[0].subject.find('Password reset') == 0
        assert mail.outbox[0].body.find('pwreset/%s' % self.uidb36) > 0

    @mock.patch.object(PasswordResetForm, 'save')
    def test_smtp_error(self, pwform_save):
        def raise_smtp(*a, **kw):
            raise SMTPRecipientsRefused(recipients=[self.user.email])
        pwform_save.side_effect = raise_smtp
        r = self.client.post(reverse('users.pw_reset'),
                             {'email': self.user.email})
        self.assertContains(r, unicode(ERROR_SEND_EMAIL))

    def _get_reset_url(self):
        return reverse('users.pw_reset_confirm',
                       args=[self.uidb36, self.token])

    def test_bad_reset_url(self):
        r = self.client.get('/users/pwreset/junk/', follow=True)
        eq_(r.status_code, 404)

        r = self.client.get(reverse('users.pw_reset_confirm',
                                    args=[self.uidb36, '12-345']))
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_('Password reset unsuccessful', doc('article h1').text())

    def test_reset_fail(self):
        url = self._get_reset_url()
        r = self.client.post(url, {'new_password1': '', 'new_password2': ''})
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(1, len(doc('ul.errorlist')))

        r = self.client.post(url, {'new_password1': 'onetwo12',
                                   'new_password2': 'twotwo22'})
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_("The two password fields didn't match.",
            doc('ul.errorlist li').text())

    def test_reset_success(self):
        url = self._get_reset_url()
        new_pw = 'fjdka387fvstrongpassword!'
        assert self.user.check_password(new_pw) is False

        r = self.client.post(url, {'new_password1': new_pw,
                               'new_password2': new_pw})
        eq_(302, r.status_code)
        eq_('http://testserver/en-US/users/pwresetcomplete', r['location'])
        self.user = User.objects.get(username='rrosario')
        assert self.user.check_password(new_pw)


class EditProfileTests(TestCaseBase):
    fixtures = ['users.json']

    def test_edit_profile(self):
        url = reverse('users.edit_profile')
        self.client.login(username='rrosario', password='testpass')
        data = {'name': 'John Doe',
                'public_email': True,
                'bio': 'my bio',
                'website': 'http://google.com/',
                'twitter': '',
                'facebook': '',
                'irc_handle': 'johndoe',
                'timezone': 'America/New_York',
                'country': 'US',
                'city': 'Disney World',
                'locale': 'en-US'}
        r = self.client.post(url, data)
        eq_(302, r.status_code)
        profile = User.objects.get(username='rrosario').get_profile()
        for key in data:
            if key != 'timezone':
                eq_(data[key], getattr(profile, key))
        eq_(data['timezone'], profile.timezone.zone)


class EditAvatarTests(TestCaseBase):
    fixtures = ['users.json']

    def setUp(self):
        super(EditAvatarTests, self).setUp()
        self.old_settings = copy(settings._wrapped.__dict__)

    def tearDown(self):
        settings._wrapped.__dict__ = self.old_settings
        user_profile = Profile.objects.get(user__username='rrosario')
        if user_profile.avatar:
            user_profile.avatar.delete()
        super(EditAvatarTests, self).tearDown()

    def test_large_avatar(self):
        settings.MAX_AVATAR_FILE_SIZE = 1024
        url = reverse('users.edit_avatar')
        self.client.login(username='rrosario', password='testpass')
        with open('apps/upload/tests/media/test.jpg') as f:
            r = self.client.post(url, {'avatar': f})
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_('"test.jpg" is too large (12KB), the limit is 1KB',
            doc('.errorlist').text())

    def test_avatar_extensions(self):
        url = reverse('users.edit_avatar')
        self.client.login(username='rrosario', password='testpass')
        with open('apps/upload/tests/media/test_invalid.ext') as f:
            r = self.client.post(url, {'avatar': f})
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_('Please upload an image with one of the following extensions: '
            'jpg, jpeg, png, gif.', doc('.errorlist').text())

    def test_upload_avatar(self):
        """Upload a valid avatar."""
        user_profile = Profile.uncached.get(user__username='rrosario')
        with open('apps/upload/tests/media/test.jpg') as f:
            user_profile.avatar.save('test_old.jpg', File(f), save=True)
        assert user_profile.avatar.name.endswith('92b516.jpg')
        old_path = user_profile.avatar.path
        assert os.path.exists(old_path), 'Old avatar is not in place.'

        url = reverse('users.edit_avatar')
        self.client.login(username='rrosario', password='testpass')
        with open('apps/upload/tests/media/test.jpg') as f:
            r = self.client.post(url, {'avatar': f})

        eq_(302, r.status_code)
        eq_('http://testserver/en-US' + reverse('users.edit_profile'),
            r['location'])
        assert not os.path.exists(old_path), 'Old avatar was not removed.'

    def test_delete_avatar(self):
        """Delete an avatar."""
        self.test_upload_avatar()

        url = reverse('users.delete_avatar')
        self.client.login(username='rrosario', password='testpass')
        r = self.client.post(url)

        user_profile = Profile.objects.get(user__username='rrosario')
        eq_(302, r.status_code)
        eq_('http://testserver/en-US' + reverse('users.edit_profile'),
            r['location'])
        eq_('', user_profile.avatar.name)


class ViewProfileTests(TestCaseBase):
    fixtures = ['users.json']

    def test_view_profile(self):
        r = self.client.get(reverse('users.profile', args=[47963]))
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(0, doc('#edit-profile-link').length)
        eq_('pcraciunoiu', doc('h1.user').text())
        # No name set and livechat_id is not different => no optional fields.
        eq_(0, doc('.contact').length)
        # Check canonical url
        eq_('/user/47963', doc('link[rel="canonical"]')[0].attrib['href'])

    def test_view_profile_mine(self):
        """Logged in, on my profile, I see an edit link."""
        self.client.login(username='pcraciunoiu', password='testpass')
        r = self.client.get(reverse('users.profile', args=[47963]))
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_('Edit settings', doc('#user-nav li:last').text())
        self.client.logout()

    def test_bio_links_nofollow(self):
        profile = Profile.objects.get(user__id=47963)
        profile.bio = 'http://getseo.com, [http://getseo.com]'
        profile.save()
        r = self.client.get(reverse('users.profile', args=[47963]))
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(2, len(doc('.bio a[rel="nofollow"]')))

    def test_num_documents(self):
        """Verify the number of documents contributed by user."""
        u = profile().user
        revision(creator=u, save=True)
        revision(creator=u, save=True)

        r = self.client.get(reverse('users.profile', args=[u.id]))
        eq_(200, r.status_code)
        assert '2 documents' in r.content


class PasswordChangeTests(TestCaseBase):
    fixtures = ['users.json']

    def setUp(self):
        super(PasswordChangeTests, self).setUp()
        self.user = User.objects.get(username='rrosario')
        self.url = reverse('users.pw_change')
        self.new_pw = 'fjdka387fvstrongpassword!'
        self.client.login(username='rrosario', password='testpass')

    def test_change_password(self):
        assert self.user.check_password(self.new_pw) is False

        r = self.client.post(self.url, {'old_password': 'testpass',
                                        'new_password1': self.new_pw,
                                        'new_password2': self.new_pw})
        eq_(302, r.status_code)
        eq_('http://testserver/en-US/users/pwchangecomplete', r['location'])
        self.user = User.objects.get(username='rrosario')
        assert self.user.check_password(self.new_pw)

    def test_bad_old_password(self):
        r = self.client.post(self.url, {'old_password': 'testpqss',
                                        'new_password1': self.new_pw,
                                        'new_password2': self.new_pw})
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_('Your old password was entered incorrectly. Please enter it '
            'again.', doc('ul.errorlist').text())

    def test_new_pw_doesnt_match(self):
        r = self.client.post(self.url, {'old_password': 'testpqss',
                                        'new_password1': self.new_pw,
                                        'new_password2': self.new_pw + '1'})
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_("Your old password was entered incorrectly. Please enter it "
            "again. The two password fields didn't match.",
            doc('ul.errorlist').text())


class ResendConfirmationTests(TestCaseBase):
    @mock.patch.object(Site.objects, 'get_current')
    def test_resend_confirmation(self, get_current):
        get_current.return_value.domain = 'testserver.com'

        RegistrationProfile.objects.create_inactive_user(
            'testuser', 'testpass', 'testuser@email.com')
        eq_(1, len(mail.outbox))

        r = self.client.post(reverse('users.resend_confirmation'),
                             {'email': 'testuser@email.com'})
        eq_(200, r.status_code)
        eq_(2, len(mail.outbox))
        assert mail.outbox[1].subject.find('Please confirm your email') == 0

    @mock.patch.object(RegistrationManager, 'send_confirmation_email')
    @mock.patch.object(Site.objects, 'get_current')
    def test_smtp_error(self, get_current, send_confirmation_email):
        get_current.return_value.domain = 'testserver.com'

        RegistrationProfile.objects.create_inactive_user(
            'testuser', 'testpass', 'testuser@email.com')

        def raise_smtp(reg_profile):
            raise SMTPRecipientsRefused(recipients=[reg_profile.user.email])
        send_confirmation_email.side_effect = raise_smtp
        r = self.client.post(reverse('users.resend_confirmation'),
                             {'email': 'testuser@email.com'})
        self.assertContains(r, unicode(ERROR_SEND_EMAIL))


class FlagProfileTests(TestCaseBase):
    fixtures = ['users.json']

    def test_flagged_and_deleted_profile(self):
        # Flag a profile and delete it
        p = User.objects.get(id=47963).get_profile()
        f = FlaggedObject(content_object=p, reason='spam', creator_id=118577)
        f.save()
        p.delete()

        # Verify flagit queue
        u = user(save=True)
        add_permission(u, FlaggedObject, 'can_moderate')
        self.client.login(username=u.username, password='testpass')
        response = get(self.client, 'flagit.queue')
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(1, len(doc('#flagged-queue form.update')))


class ForgotUsernameTests(TestCaseBase):
    """Tests for the Forgot Username flow."""

    def test_GET(self):
        r = self.client.get(reverse('users.forgot_username'))
        eq_(200, r.status_code)

    @mock.patch.object(Site.objects, 'get_current')
    def test_POST(self, get_current):
        get_current.return_value.domain = 'testserver.com'
        u = user(save=True, email='a@b.com', is_active=True)

        r = self.client.post(reverse('users.forgot_username'),
                             {'email': u.email})
        eq_(302, r.status_code)
        eq_('http://testserver/en-US/users/login', r['location'])

        # Verify email
        eq_(1, len(mail.outbox))
        assert mail.outbox[0].subject.find('Your username on') == 0
        assert mail.outbox[0].body.find(u.username) > 0
