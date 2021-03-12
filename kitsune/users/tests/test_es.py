# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from django.core.management import call_command
from nose.tools import eq_

from kitsune.questions.tests import AnswerFactory
from kitsune.search.tests.test_es import ElasticTestCase
from kitsune.users.models import UserMappingType
from kitsune.users.tests import ProfileFactory, UserFactory
from kitsune.wiki.tests import RevisionFactory


class UserSearchTests(ElasticTestCase):
    def test_add_and_delete(self):
        """Adding a user with a profile should add it to the index.

        Deleting should delete it.
        """
        p = ProfileFactory()
        self.refresh()
        eq_(UserMappingType.search().count(), 1)

        p.user.delete()
        self.refresh()
        eq_(UserMappingType.search().count(), 0)

    def test_data_in_index(self):
        """Verify the data we are indexing."""
        u = UserFactory(username="r1cky", email="r@r.com", profile__name="Rick Róss")

        self.refresh()

        eq_(UserMappingType.search().count(), 1)
        data = UserMappingType.search()[0]
        eq_(data["username"], u.username)
        eq_(data["display_name"], u.profile.name)

        u = UserFactory(username="willkg", email="w@w.com", profile__name="Will Cage")
        self.refresh()
        eq_(UserMappingType.search().count(), 2)

    def test_suggest_completions(self):
        u1 = UserFactory(username="r1cky", profile__name="Rick Róss")
        u2 = UserFactory(username="Willkg", profile__name="Will Cage")

        self.refresh()
        eq_(UserMappingType.search().count(), 2)

        results = UserMappingType.suggest_completions("wi")
        eq_(1, len(results))
        eq_("Will Cage (Willkg)", results[0]["text"])
        eq_(u2.id, results[0]["payload"]["user_id"])

        results = UserMappingType.suggest_completions("R1")
        eq_(1, len(results))
        eq_("Rick Róss (r1cky)", results[0]["text"])
        eq_(u1.id, results[0]["payload"]["user_id"])

        # Add another Ri....
        UserFactory(username="richard", profile__name="Richard Smith")

        self.refresh()
        eq_(UserMappingType.search().count(), 3)

        results = UserMappingType.suggest_completions("ri")
        eq_(2, len(results))
        texts = [r["text"] for r in results]
        assert "Rick Róss (r1cky)" in texts
        assert "Richard Smith (richard)" in texts

        results = UserMappingType.suggest_completions("Rick Ró")
        eq_(1, len(results))
        texts = [r["text"] for r in results]
        eq_("Rick Róss (r1cky)", results[0]["text"])

    def test_suggest_completions_numbers(self):
        u1 = UserFactory(username="1337mike", profile__name="Elite Mike")
        UserFactory(username="crazypants", profile__name="Crazy Pants")

        self.refresh()
        eq_(UserMappingType.search().count(), 2)

        results = UserMappingType.suggest_completions("13")
        eq_(1, len(results))
        eq_("Elite Mike (1337mike)", results[0]["text"])
        eq_(u1.id, results[0]["payload"]["user_id"])

    def test_query_username_with_numbers(self):
        u = UserFactory(username="1337miKE", profile__name="Elite Mike")
        UserFactory(username="mike", profile__name="NotElite Mike")

        self.refresh()

        eq_(UserMappingType.search().query(iusername__match="1337mike").count(), 1)
        data = UserMappingType.search().query(iusername__match="1337mike")[0]
        eq_(data["username"], u.username)
        eq_(data["display_name"], u.profile.name)

    def test_query_display_name_with_whitespace(self):
        UserFactory(username="1337miKE", profile__name="Elite Mike")
        UserFactory(username="mike", profile__name="NotElite Mike")

        self.refresh()

        eq_(UserMappingType.search().count(), 2)
        eq_(UserMappingType.search().query(idisplay_name__match_whitespace="elite").count(), 1)

    def test_last_contribution_date(self):
        """Verify the last_contribution_date field works properly."""
        u = UserFactory(username="satdav")
        self.refresh()

        data = UserMappingType.search().query(username__match="satdav")[0]
        assert not data["last_contribution_date"]

        # Add a Support Forum answer. It should be the last contribution.
        d = datetime(2014, 1, 2)
        AnswerFactory(creator=u, created=d)
        u.profile.save()  # we need to resave the profile to force a reindex
        self.refresh()

        data = UserMappingType.search().query(username__match="satdav")[0]
        eq_(data["last_contribution_date"], d)

        # Add a Revision edit. It should be the last contribution.
        d = datetime(2014, 1, 3)
        RevisionFactory(created=d, creator=u)
        u.profile.save()  # we need to resave the profile to force a reindex
        self.refresh()

        data = UserMappingType.search().query(username__match="satdav")[0]
        eq_(data["last_contribution_date"], d)

        # Add a Revision review. It should be the last contribution.
        d = datetime(2014, 1, 4)
        RevisionFactory(reviewed=d, reviewer=u)

        u.profile.save()  # we need to resave the profile to force a reindex
        self.refresh()

        data = UserMappingType.search().query(username__match="satdav")[0]
        eq_(data["last_contribution_date"], d)

    def test_reindex_users_that_contributed_yesterday(self):
        yesterday = datetime.now() - timedelta(days=1)

        # Verify for answers.
        u = UserFactory(username="answerer")
        AnswerFactory(creator=u, created=yesterday)

        call_command("reindex_users_that_contributed_yesterday")
        self.refresh()

        data = UserMappingType.search().query(username__match="answerer")[0]
        eq_(data["last_contribution_date"].date(), yesterday.date())

        # Verify for edits.
        u = UserFactory(username="editor")
        RevisionFactory(creator=u, created=yesterday)

        call_command("reindex_users_that_contributed_yesterday")
        self.refresh()

        data = UserMappingType.search().query(username__match="editor")[0]
        eq_(data["last_contribution_date"].date(), yesterday.date())

        # Verify for reviews.
        u = UserFactory(username="reviewer")
        RevisionFactory(reviewer=u, reviewed=yesterday)

        call_command("reindex_users_that_contributed_yesterday")
        self.refresh()

        data = UserMappingType.search().query(username__match="reviewer")[0]
        eq_(data["last_contribution_date"].date(), yesterday.date())
