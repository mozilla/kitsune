import copy

from django.conf import settings
from django.db import models
from django.db.utils import DatabaseError
from django.test import TestCase, override_settings
from pyquery import PyQuery as pq

from kitsune.questions.models import Question
from kitsune.sumo.urlresolvers import reverse
from kitsune.users.tests import UserFactory


class ReadOnlyModeTest(TestCase):
    extra = ("kitsune.sumo.middleware.ReadOnlyMiddleware",)

    def setUp(self):
        # This has to be done before the db goes into read only mode.
        self.user = UserFactory(password="testpass")

        models.signals.pre_save.connect(self.db_error)
        models.signals.pre_delete.connect(self.db_error)
        self.old_settings = copy.copy(settings._wrapped.__dict__)

    def tearDown(self):
        models.signals.pre_save.disconnect(self.db_error)
        models.signals.pre_delete.disconnect(self.db_error)

    def db_error(self, *args, **kwargs):
        raise DatabaseError("You can't do this in read-only mode.")

    @override_settings(READ_ONLY=True)
    def test_db_error(self):
        with self.assertRaises(DatabaseError):
            Question.objects.create(id=12)

    @override_settings(READ_ONLY=True)
    def test_login_error(self):
        # This tries to do a db write.
        url = reverse("users.login", locale="en-US")
        r = self.client.post(
            url,
            {
                "username": self.user.username,
                "password": "testpass",
            },
            follow=True,
        )
        self.assertEqual(r.status_code, 503)
        title = pq(r.content)("title").text()
        assert title.startswith("Maintenance in progress"), title

    @override_settings(READ_ONLY=True)
    def test_bail_on_post(self):
        r = self.client.post("/en-US/questions")
        self.assertEqual(r.status_code, 503)
        title = pq(r.content)("title").text()
        assert title.startswith("Maintenance in progress"), title
