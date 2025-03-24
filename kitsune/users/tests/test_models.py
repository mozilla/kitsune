import logging

from kitsune.sumo.tests import TestCase
from kitsune.users.forms import SettingsForm
from kitsune.users.models import Setting
from kitsune.users.tests import UserFactory

log = logging.getLogger("k.users")


class UserSettingsTests(TestCase):
    def setUp(self):
        self.u = UserFactory()

    def test_non_existant_setting(self):
        form = SettingsForm()
        bad_setting = "doesnt_exist"
        assert bad_setting not in list(form.fields.keys())
        with self.assertRaises(KeyError):
            Setting.get_for_user(self.u, bad_setting)

    def test_default_values(self):
        self.assertEqual(0, Setting.objects.count())
        keys = list(SettingsForm.base_fields.keys())
        for setting in keys:
            SettingsForm.base_fields[setting]
            self.assertEqual(False, Setting.get_for_user(self.u, setting))


class ProfileTests(TestCase):
    def setUp(self):
        self.user = UserFactory()

    def test_has_content_no_content(self):
        """Test that has_content returns False when user has no content."""
        self.assertFalse(self.user.profile.has_content)

    def test_has_content_with_answers(self):
        """Test that has_content returns True when user has answers."""
        from kitsune.questions.tests import AnswerFactory

        # Initially no content
        self.assertFalse(self.user.profile.has_content)

        # Add an answer
        AnswerFactory(creator=self.user)

        # Now should have content
        self.assertTrue(self.user.profile.has_content)

    def test_has_content_with_revision(self):
        """Test that has_content returns True when user has created revisions."""
        from kitsune.wiki.tests import RevisionFactory

        # Initially no content
        self.assertFalse(self.user.profile.has_content)

        # Add a revision
        RevisionFactory(creator=self.user)

        # Now should have content
        self.assertTrue(self.user.profile.has_content)

    def test_has_content_with_question(self):
        """Test that has_content returns True when user has questions."""
        from kitsune.questions.tests import QuestionFactory

        # Initially no content
        self.assertFalse(self.user.profile.has_content)

        # Add a question
        QuestionFactory(creator=self.user)

        # Now should have content
        self.assertTrue(self.user.profile.has_content)
