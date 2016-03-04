from copy import copy
import os
from smtplib import SMTPRecipientsRefused

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.models import Site
from django.core import mail
from django.core.files import File
from django.utils.http import int_to_base36

import mock
from nose.tools import eq_
from pyquery import PyQuery as pq
from tidings.models import Watch

from kitsune.flagit.models import FlaggedObject
from kitsune.kbadge.tests import AwardFactory, BadgeFactory
from kitsune.questions.events import QuestionReplyEvent
from kitsune.questions.tests import QuestionFactory
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.templatetags.jinja_helpers import urlparams
from kitsune.sumo.tests import post, get
from kitsune.users import ERROR_SEND_EMAIL
from kitsune.users.forms import PasswordResetForm
from kitsune.users.models import (
    Profile, RegistrationProfile, RegistrationManager)
from kitsune.users.tests import (
    TestCaseBase, UserFactory, add_permission, GroupFactory)
from kitsune.wiki.tests import RevisionFactory


class LoginTests(TestCaseBase):
    """Login tests."""

    def setUp(self):
        super(LoginTests, self).setUp()
        self.u = UserFactory()

    def test_login_bad_password(self):
        '''Test login with a good username and bad password.'''
        response = post(self.client, 'users.login',
                        {'username': self.u.username, 'password': 'foobar'})
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

    def test_login_password_disabled(self):
        """Test logging in as a user with PASSWORD_DISABLED doesn't 500."""
        self.u.set_unusable_password()
        self.u.save()
        response = self.client.post(reverse('users.login'),
                                    {'username': self.u.username,
                                     'password': 'testpass'})
        eq_(200, response.status_code)

    def test_login(self):
        '''Test a valid login.'''
        response = self.client.post(reverse('users.login'),
                                    {'username': self.u.username,
                                     'password': 'testpass'})
        eq_(302, response.status_code)
        eq_('http://testserver' +
            reverse('home', locale=settings.LANGUAGE_CODE) + '?fpa=1',
            response['location'])

    def test_login_next_parameter(self):
        '''Test with a valid ?next=url parameter.'''
        next = '/kb/new'

        # Verify that next parameter is set in form hidden field.
        response = self.client.get(
            urlparams(reverse('users.login'), next=next), follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        eq_(next, doc('#login input[name="next"]')[0].attrib['value'])

        # Verify that it gets used on form POST.
        response = self.client.post(reverse('users.login'),
                                    {'username': self.u.username,
                                     'password': 'testpass',
                                     'next': next})
        eq_(302, response.status_code)
        eq_('http://testserver' + next + '?fpa=1', response['location'])

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
        eq_(valid_next, doc('#login input[name="next"]')[0].attrib['value'])

        # Verify that it gets used on form POST.
        response = self.client.post(reverse('users.login'),
                                    {'username': self.u.username,
                                     'password': 'testpass',
                                     'next': invalid_next})
        eq_(302, response.status_code)
        eq_('http://testserver' + valid_next + '?fpa=1', response['location'])

    def test_ga_custom_variable_on_registered_login(self):
        """After logging in, there should be a ga-push data attr on body."""
        user_ = UserFactory()

        # User should be "Registered":
        response = self.client.post(reverse('users.login'),
                                    {'username': user_.username,
                                     'password': 'testpass'},
                                    follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        assert '"Registered"' in doc('body').attr('data-ga-push')

    def test_ga_custom_variable_on_contributor_login(self):
        """After logging in, there should be a ga-push data attr on body."""
        user_ = UserFactory()

        # Add user to Contributors and so should be "Contributor":
        user_.groups.add(GroupFactory(name='Contributors'))
        response = self.client.post(reverse('users.login'),
                                    {'username': user_.username,
                                     'password': 'testpass'},
                                    follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        assert '"Contributor"' in doc('body').attr('data-ga-push')

    def test_ga_custom_variable_on_admin_login(self):
        """After logging in, there should be a ga-push data attr on body."""
        user_ = UserFactory()

        # Add user to Administrators and so should be "Contributor - Admin":
        user_.groups.add(GroupFactory(name='Administrators'))
        response = self.client.post(reverse('users.login'),
                                    {'username': user_.username,
                                     'password': 'testpass'},
                                    follow=True)
        eq_(200, response.status_code)
        doc = pq(response.content)
        assert '"Contributor - Admin"' in doc('body').attr('data-ga-push')

    def test_login_mobile_csrf(self):
        """The mobile login view should have a CSRF token."""
        response = self.client.get(reverse('users.login'), {'mobile': 1})
        eq_(200, response.status_code)
        doc = pq(response.content)
        assert doc('#content form input[name="csrfmiddlewaretoken"]')


class PasswordResetTests(TestCaseBase):

    def setUp(self):
        super(PasswordResetTests, self).setUp()
        self.u = UserFactory(email="valid@email.com")
        self.uidb36 = int_to_base36(self.u.id)
        self.token = default_token_generator.make_token(self.u)
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
                             {'email': self.u.email})
        eq_(302, r.status_code)
        eq_('http://testserver/en-US/users/pwresetsent', r['location'])
        eq_(1, len(mail.outbox))
        assert mail.outbox[0].subject.find('Password reset') == 0
        assert mail.outbox[0].body.find('pwreset/%s' % self.uidb36) > 0

    @mock.patch.object(PasswordResetForm, 'save')
    def test_smtp_error(self, pwform_save):
        def raise_smtp(*a, **kw):
            raise SMTPRecipientsRefused(recipients=[self.u.email])
        pwform_save.side_effect = raise_smtp
        r = self.client.post(reverse('users.pw_reset'),
                             {'email': self.u.email})
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
        assert self.u.check_password(new_pw) is False

        r = self.client.post(url, {'new_password1': new_pw,
                                   'new_password2': new_pw})
        eq_(302, r.status_code)
        eq_('http://testserver/en-US/users/pwresetcomplete', r['location'])
        self.u = User.objects.get(username=self.u.username)
        assert self.u.check_password(new_pw)

    def test_reset_user_with_unusable_password(self):
        """Verify that user's with unusable passwords can reset them."""
        self.u.set_unusable_password()
        self.u.save()
        self.test_success()


class EditProfileTests(TestCaseBase):

    def test_edit_my_ProfileFactory(self):
        u = UserFactory()
        url = reverse('users.edit_my_profile')
        self.client.login(username=u.username, password='testpass')
        data = {'name': 'John Doe',
                'public_email': True,
                'bio': 'my bio',
                'website': 'http://google.com/',
                'twitter': '',
                'facebook': '',
                'mozillians': '',
                'irc_handle': 'johndoe',
                'timezone': 'America/New_York',
                'country': 'US',
                'city': 'Disney World',
                'locale': 'en-US'}
        r = self.client.post(url, data)
        eq_(302, r.status_code)
        profile = Profile.objects.get(user=u)
        for key in data:
            if key != 'timezone':
                eq_(data[key], getattr(profile, key))
        eq_(data['timezone'], profile.timezone.zone)

    def test_user_cant_edit_others_profile_without_permission(self):
        u1 = UserFactory()
        url = reverse('users.edit_profile', args=[u1.username])

        u2 = UserFactory()
        self.client.login(username=u2.username, password='testpass')

        # Try GET
        r = self.client.get(url)
        eq_(403, r.status_code)

        # Try POST
        r = self.client.post(url, {})
        eq_(403, r.status_code)

    def test_user_can_edit_others_profile_with_permission(self):
        u1 = UserFactory()
        url = reverse('users.edit_profile', args=[u1.username])

        u2 = UserFactory()
        add_permission(u2, Profile, 'change_profile')
        self.client.login(username=u2.username, password='testpass')

        # Try GET
        r = self.client.get(url)
        eq_(200, r.status_code)

        # Try POST
        data = {'name': 'John Doe',
                'public_email': True,
                'bio': 'my bio',
                'website': 'http://google.com/',
                'twitter': '',
                'facebook': '',
                'mozillians': '',
                'irc_handle': 'johndoe',
                'timezone': 'America/New_York',
                'country': 'US',
                'city': 'Disney World',
                'locale': 'en-US'}
        r = self.client.post(url, data)
        eq_(302, r.status_code)
        profile = Profile.objects.get(user=u1)
        for key in data:
            if key != 'timezone':
                eq_(data[key], getattr(profile, key))
        eq_(data['timezone'], profile.timezone.zone)


class EditAvatarTests(TestCaseBase):

    def setUp(self):
        super(EditAvatarTests, self).setUp()
        self.old_settings = copy(settings._wrapped.__dict__)
        self.u = UserFactory()

    def tearDown(self):
        settings._wrapped.__dict__ = self.old_settings
        user_profile = Profile.objects.get(user__username=self.u.username)
        if user_profile.avatar:
            user_profile.avatar.delete()
        super(EditAvatarTests, self).tearDown()

    def test_large_avatar(self):
        settings.MAX_AVATAR_FILE_SIZE = 1024
        url = reverse('users.edit_avatar')
        self.client.login(username=self.u.username, password='testpass')
        with open('kitsune/upload/tests/media/test.jpg') as f:
            r = self.client.post(url, {'avatar': f})
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_('"test.jpg" is too large (12KB), the limit is 1KB',
            doc('.errorlist').text())

    def test_avatar_extensions(self):
        url = reverse('users.edit_avatar')
        self.client.login(username=self.u.username, password='testpass')
        with open('kitsune/upload/tests/media/test_invalid.ext') as f:
            r = self.client.post(url, {'avatar': f})
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_('Please upload an image with one of the following extensions: '
            'jpg, jpeg, png, gif.', doc('.errorlist').text())

    def test_upload_avatar(self):
        """Upload a valid avatar."""
        user_profile = Profile.objects.get(user__username=self.u.username)
        with open('kitsune/upload/tests/media/test.jpg') as f:
            user_profile.avatar.save('test_old.jpg', File(f), save=True)
        assert user_profile.avatar.name.endswith('92b516.jpg')
        old_path = user_profile.avatar.path
        assert os.path.exists(old_path), 'Old avatar is not in place.'

        url = reverse('users.edit_avatar')
        self.client.login(username=self.u.username, password='testpass')
        with open('kitsune/upload/tests/media/test.jpg') as f:
            r = self.client.post(url, {'avatar': f})

        eq_(302, r.status_code)
        eq_('http://testserver/en-US' + reverse('users.edit_my_profile'),
            r['location'])
        assert not os.path.exists(old_path), 'Old avatar was not removed.'

    def test_delete_avatar(self):
        """Delete an avatar."""
        self.test_upload_avatar()

        url = reverse('users.delete_avatar')
        self.client.login(username=self.u.username, password='testpass')
        r = self.client.post(url)

        user_profile = Profile.objects.get(user__username=self.u.username)
        eq_(302, r.status_code)
        eq_('http://testserver/en-US' + reverse('users.edit_my_profile'),
            r['location'])
        eq_('', user_profile.avatar.name)


class ViewProfileTests(TestCaseBase):

    def setUp(self):
        self.u = UserFactory(profile__name='', profile__website='')
        self.profile = self.u.profile

    def test_view_ProfileFactory(self):
        r = self.client.get(reverse('users.profile', args=[self.u.username]))
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(0, doc('#edit-profile-link').length)
        eq_(self.u.username, doc('h1.user').text())
        # No name set => no optional fields.
        eq_(0, doc('.contact').length)
        # Check canonical url
        eq_('/user/%s' % self.u.username,
            doc('link[rel="canonical"]')[0].attrib['href'])

    def test_view_profile_mine(self):
        """Logged in, on my profile, I see an edit link."""
        self.client.login(username=self.u.username, password='testpass')
        r = self.client.get(reverse('users.profile', args=[self.u.username]))
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_('Manage watch list', doc('#user-nav li:last').text())
        self.client.logout()

    def test_bio_links_nofollow(self):
        self.profile.bio = 'http://getseo.com, [http://getseo.com]'
        self.profile.save()
        r = self.client.get(reverse('users.profile', args=[self.u.username]))
        eq_(200, r.status_code)
        doc = pq(r.content)
        eq_(2, len(doc('.bio a[rel="nofollow"]')))

    def test_num_documents(self):
        """Verify the number of documents contributed by user."""
        u = UserFactory()
        RevisionFactory(creator=u)
        RevisionFactory(creator=u)

        r = self.client.get(reverse('users.profile', args=[u.username]))
        eq_(200, r.status_code)
        assert '2 documents' in r.content

    def test_deactivate_button(self):
        """Check that the deactivate button is shown appropriately"""
        u = UserFactory()
        r = self.client.get(reverse('users.profile', args=[u.username]))
        assert 'Deactivate this user' not in r.content

        add_permission(self.u, Profile, 'deactivate_users')
        self.client.login(username=self.u.username, password='testpass')
        r = self.client.get(reverse('users.profile', args=[u.username]))
        assert 'Deactivate this user' in r.content

        u.is_active = False
        u.save()
        r = self.client.get(reverse('users.profile', args=[u.username]))
        assert 'This user has been deactivated.' in r.content

        r = self.client.get(reverse('users.profile', args=[self.u.username]))
        assert 'Deactivate this user' not in r.content

    def test_badges_listed(self):
        """Verify that awarded badges appear on the profile page."""
        badge_title = 'awesomesauce badge'
        b = BadgeFactory(title=badge_title)
        u = UserFactory()
        AwardFactory(user=u, badge=b)
        r = self.client.get(reverse('users.profile', args=[u.username]))
        assert badge_title in r.content


class PasswordChangeTests(TestCaseBase):

    def setUp(self):
        super(PasswordChangeTests, self).setUp()
        self.u = UserFactory()
        self.url = reverse('users.pw_change')
        self.new_pw = 'fjdka387fvstrongpassword!'
        self.client.login(username=self.u.username, password='testpass')

    def test_change_password(self):
        assert self.u.check_password(self.new_pw) is False

        r = self.client.post(self.url, {'old_password': 'testpass',
                                        'new_password1': self.new_pw,
                                        'new_password2': self.new_pw})
        eq_(302, r.status_code)
        eq_('http://testserver/en-US/users/pwchangecomplete', r['location'])
        self.u = User.objects.get(username=self.u.username)
        assert self.u.check_password(self.new_pw)

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
        eq_("The two password fields didn't match. Your old password was "
            "entered incorrectly. Please enter it again.",
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

    @mock.patch.object(Site.objects, 'get_current')
    def test_resend_confirmation_already_activated(self, get_current):
        get_current.return_value.domain = 'testserver.com'
        user_ = RegistrationProfile.objects.create_inactive_user(
            'testuser', 'testpass', 'testuser@email.com')

        # Activate the user
        key = RegistrationProfile.objects.all()[0].activation_key
        url = reverse('users.activate', args=[user_.id, key])
        response = self.client.get(url, follow=True)
        eq_(200, response.status_code)
        user_ = User.objects.get(pk=user_.pk)
        assert user_.is_active

        # Delete RegistrationProfile objects.
        RegistrationProfile.objects.all().delete()

        # Resend the confirmation email
        r = self.client.post(reverse('users.resend_confirmation'),
                             {'email': 'testuser@email.com'})
        eq_(200, r.status_code)
        eq_(2, len(mail.outbox))
        eq_(mail.outbox[1].subject.find('Account already activated'), 0)

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

    def test_flagged_and_deleted_ProfileFactory(self):
        u = UserFactory()
        p = u.profile
        flag_user = UserFactory()
        # Flag a profile and delete it
        f = FlaggedObject(content_object=p,
                          reason='spam', creator_id=flag_user.id)
        f.save()
        p.delete()

        # Verify flagit queue
        u = UserFactory()
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
        u = UserFactory(email='a@b.com', is_active=True)

        r = self.client.post(reverse('users.forgot_username'),
                             {'email': u.email})
        eq_(302, r.status_code)
        eq_('http://testserver/en-US/users/login', r['location'])

        # Verify email
        eq_(1, len(mail.outbox))
        assert mail.outbox[0].subject.find('Your username on') == 0
        assert mail.outbox[0].body.find(u.username) > 0


class EditWatchListTests(TestCaseBase):
    """Test manage watch list"""

    def setUp(self):
        self.user = UserFactory()
        self.client.login(username=self.user.username, password='testpass')

        self.question = QuestionFactory(creator=self.user)
        QuestionReplyEvent.notify(self.user, self.question)

    def test_GET(self):
        r = self.client.get(reverse('users.edit_watch_list'))
        eq_(200, r.status_code)
        assert u'question: ' + self.question.title in r.content.decode('utf8')

    def test_POST(self):
        w = Watch.objects.get(object_id=self.question.id, user=self.user)
        eq_(w.is_active, True)

        self.client.post(reverse('users.edit_watch_list'))
        w = Watch.objects.get(object_id=self.question.id, user=self.user)
        eq_(w.is_active, False)

        self.client.post(reverse('users.edit_watch_list'), {
            'watch_%s' % w.id: '1'})
        w = Watch.objects.get(object_id=self.question.id, user=self.user)
        eq_(w.is_active, True)
