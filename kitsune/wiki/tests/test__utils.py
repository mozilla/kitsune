from datetime import date, timedelta

from nose.tools import eq_

from kitsune.sumo.tests import TestCase
from kitsune.users.tests import user
from kitsune.wiki.tests import revision, document
from kitsune.wiki.utils import active_contributors


class ActiveContributorsTestCase(TestCase):

    def test_active_contributors(self):
        start_date = date.today() - timedelta(days=10)
        before_start = start_date - timedelta(days=1)

        # Create some revisions to test with.

        # 3 'en-US' contributors:
        d = document(locale='en-US', save=True)
        u = user(save=True)
        revision(document=d, is_approved=True, reviewer=u, save=True)
        revision(document=d, creator=u, save=True)
        revision(document=d, created=start_date, save=True)
        # Add one that shouldn't count:
        en_us_old = revision(document=d, created=before_start, save=True)

        # 4 'es' contributors:
        d = document(locale='es', save=True)
        revision(document=d, is_approved=True, reviewer=u, save=True)
        revision(document=d, creator=u, reviewer=user(save=True), save=True)
        revision(document=d, created=start_date, save=True)
        revision(document=d, save=True)
        # Add one that shouldn't count:
        es_old = revision(document=d, created=before_start, save=True)

        # Verify results!
        en_us_contributors = active_contributors(
            from_date=start_date, locale='en-US')
        es_contributors = active_contributors(
            from_date=start_date, locale='es')
        all_contributors = active_contributors(from_date=start_date)

        eq_(3, len(en_us_contributors))
        assert u in en_us_contributors
        assert en_us_old.creator not in en_us_contributors

        eq_(4, len(es_contributors))
        assert u in es_contributors
        assert es_old.creator not in es_contributors

        eq_(6, len(all_contributors))
        assert u in all_contributors
        assert en_us_old.creator not in all_contributors
        assert es_old.creator not in all_contributors
