# -*- coding: utf-8 -*-
from datetime import date, timedelta

from django.conf import settings
from django.core.management import call_command
from nose.tools import eq_

from kitsune.dashboards.management.commands.cache_most_unhelpful_kb_articles import (
    _get_current_unhelpful, _get_old_unhelpful)
from kitsune.dashboards.models import (L10N_ALL_CODE, L10N_TOP20_CODE,
                                       L10N_TOP100_CODE, WikiMetric)
from kitsune.products.tests import ProductFactory
from kitsune.sumo.redis_utils import RedisError, redis_client
from kitsune.sumo.tests import SkipTest, TestCase
from kitsune.users.tests import UserFactory
from kitsune.wiki.tests import (ApprovedRevisionFactory, DocumentFactory,
                                HelpfulVoteFactory, RevisionFactory)


def _add_vote_in_past(rev, vote, days_back):
    HelpfulVoteFactory(
        revision=rev,
        helpful=vote,
        created=date.today() - timedelta(days=days_back))


def _make_backdated_revision(backdate):
    return RevisionFactory(created=date.today() - timedelta(days=backdate))


class TopUnhelpfulArticlesTests(TestCase):
    def test_no_old_articles(self):
        """Make sure _get_old_articles() returns nothing with no votes."""
        result = _get_old_unhelpful()
        eq_(0, len(result))

    def test_no_current_articles(self):
        """Make sure _get_current_articles() returns nothing with no votes.
        """
        result = _get_current_unhelpful({})
        eq_(0, len(result))

    def test_old_articles(self):
        """Returns unhelpful votes within time range"""
        r = _make_backdated_revision(10)

        # Add 4 no votes 1.5 weeks ago
        for x in range(4):
            _add_vote_in_past(r, 0, 10)

        # Add 1 yes vote 1.5 weeks ago
        _add_vote_in_past(r, 1, 10)

        result = _get_old_unhelpful()
        eq_(1, len(result))
        self.assertAlmostEqual(0.2, result[r.document.id]['percentage'])
        eq_(5, result[r.document.id]['total'])

    def test_old_articles_helpful(self):
        """Doesn't return helpful votes within range"""
        r = _make_backdated_revision(90)

        for x in range(0, 4):
            _add_vote_in_past(r, 1, 10)

        _add_vote_in_past(r, 0, 10)

        result = _get_old_unhelpful()
        eq_(0, len(result))

    def test_current_articles(self):
        """Returns unhelpful votes within time range"""
        r = _make_backdated_revision(90)

        for x in range(0, 3):
            _add_vote_in_past(r, 0, 3)

        for x in range(0, 2):
            _add_vote_in_past(r, 1, 3)

        old_data = {r.document.id: {'percentage': 0.2, 'total': 5.0}}

        result = _get_current_unhelpful(old_data)
        eq_(1, len(result))
        self.assertAlmostEqual(0.4, result[r.document.id]['currperc'])
        self.assertAlmostEqual(0.4 - old_data[r.document.id]['percentage'],
                               result[r.document.id]['diffperc'])
        eq_(5, result[r.document.id]['total'])

    def test_current_articles_helpful(self):
        """Doesn't return helpful votes within time range"""
        r = _make_backdated_revision(90)

        for x in range(0, 3):
            _add_vote_in_past(r, 1, 3)

        for x in range(0, 2):
            _add_vote_in_past(r, 0, 3)

        old_data = {r.document.id: {'percentage': 0.2, 'total': 5.0}}

        result = _get_current_unhelpful(old_data)
        eq_(0, len(result))

    def test_current_articles_not_in_old(self):
        """Unhelpful articles in current but not in old works"""
        r = _make_backdated_revision(90)

        for x in range(0, 3):
            _add_vote_in_past(r, 0, 3)

        for x in range(0, 2):
            _add_vote_in_past(r, 1, 3)

        old_data = {}

        result = _get_current_unhelpful(old_data)

        eq_(1, len(result))
        self.assertAlmostEqual(0.4, result[r.document.id]['currperc'])
        self.assertAlmostEqual(0, result[r.document.id]['diffperc'])
        eq_(5, result[r.document.id]['total'])


class TopUnhelpfulArticlesCommandTests(TestCase):
    def setUp(self):
        super(TopUnhelpfulArticlesCommandTests, self).setUp()
        self.REDIS_KEY = settings.HELPFULVOTES_UNHELPFUL_KEY
        try:
            self.redis = redis_client('helpfulvotes')
            self.redis.flushdb()
        except RedisError:
            raise SkipTest

    def tearDown(self):
        try:
            self.redis.flushdb()
        except (KeyError, AttributeError):
            raise SkipTest
        super(TopUnhelpfulArticlesCommandTests, self).tearDown()

    def test_no_articles(self):
        """No articles returns no unhelpful articles."""
        call_command('cache_most_unhelpful_kb_articles')
        eq_(0, self.redis.llen(self.REDIS_KEY))

    def test_caching_unhelpful(self):
        """Command should get the unhelpful articles."""
        r = _make_backdated_revision(90)

        for x in range(0, 3):
            _add_vote_in_past(r, 0, 3)

        for x in range(0, 2):
            _add_vote_in_past(r, 1, 3)

        call_command('cache_most_unhelpful_kb_articles')

        eq_(1, self.redis.llen(self.REDIS_KEY))
        result = self.redis.lrange(self.REDIS_KEY, 0, 1)
        eq_('%d::%.1f::%.1f::%.1f::%.1f::%s::%s' %
            (r.document.id, 5.0, 0.4, 0.0, 0.0, r.document.slug,
             r.document.title),
            result[0].decode('utf-8'))

    def test_caching_helpful(self):
        """Command should ignore the helpful articles."""
        r = _make_backdated_revision(90)

        for x in range(0, 3):
            _add_vote_in_past(r, 1, 3)

        for x in range(0, 2):
            _add_vote_in_past(r, 0, 3)

        call_command('cache_most_unhelpful_kb_articles')

        eq_(0, self.redis.llen(self.REDIS_KEY))

    def test_caching_changed_helpfulness(self):
        """Changed helpfulness should be calculated correctly."""
        r = _make_backdated_revision(90)

        for x in range(0, 4):
            _add_vote_in_past(r, 0, 10)

        for x in range(0, 1):
            _add_vote_in_past(r, 1, 10)

        for x in range(0, 3):
            _add_vote_in_past(r, 0, 3)

        for x in range(0, 2):
            _add_vote_in_past(r, 1, 3)

        call_command('cache_most_unhelpful_kb_articles')

        eq_(1, self.redis.llen(self.REDIS_KEY))
        result = self.redis.lrange(self.REDIS_KEY, 0, 1)
        eq_('%d::%.1f::%.1f::%.1f::%.1f::%s::%s' %
            (r.document.id, 5.0, 0.4, 0.2, 0.0, r.document.slug,
             r.document.title),
            result[0].decode('utf-8'))

    def test_caching_sorting(self):
        """Tests if Bayesian Average sorting works correctly."""
        # This should be at the bottom.
        r = _make_backdated_revision(90)

        for x in range(0, 26):
            _add_vote_in_past(r, 1, 3)

        for x in range(0, 76):
            _add_vote_in_past(r, 0, 3)

        # This should be at the top.
        r2 = _make_backdated_revision(90)

        for x in range(0, 61):
            _add_vote_in_past(r2, 1, 3)

        for x in range(0, 181):
            _add_vote_in_past(r2, 0, 3)

        # This should be in the middle.
        r3 = _make_backdated_revision(90)

        for x in range(0, 31):
            _add_vote_in_past(r3, 1, 3)

        for x in range(0, 91):
            _add_vote_in_past(r3, 0, 3)

        call_command('cache_most_unhelpful_kb_articles')

        eq_(3, self.redis.llen(self.REDIS_KEY))
        result = self.redis.lrange(self.REDIS_KEY, 0, 3)
        assert '%d::%.1f:' % (r2.document.id, 242.0) in result[0].decode()
        assert '%d::%.1f:' % (r3.document.id, 122.0) in result[1].decode()
        assert '%d::%.1f:' % (r.document.id, 102.0) in result[2].decode()


class L10nMetricsTests(TestCase):

    def test_update_l10n_coverage_metrics(self):
        """Test the command that updates l10n coverage metrics."""
        p = ProductFactory(visible=True)

        # Create en-US documents.
        revisions = RevisionFactory.create_batch(
            20,
            is_approved=True,
            is_ready_for_localization=True,
            document__products=[p],
            document__locale='en-US')

        r1 = revisions[0]
        r2 = revisions[1]

        # Translate one to es.
        d = DocumentFactory(parent=r1.document, locale='es')
        ApprovedRevisionFactory(document=d, based_on=r1)

        # Translate two to de.
        d = DocumentFactory(parent=r1.document, locale='de')
        ApprovedRevisionFactory(document=d, based_on=r1)
        d = DocumentFactory(parent=r2.document, locale='de')
        ApprovedRevisionFactory(document=d, based_on=r2)

        # Translate all to ru.
        for r in revisions:
            d = DocumentFactory(parent=r.document, locale='ru')
            RevisionFactory(document=d, based_on=r, is_approved=True)

        # Call the management command
        call_command('update_l10n_coverage_metrics')

        # Verify es metrics.
        eq_(6, WikiMetric.objects.filter(locale='es').count())
        eq_(5.0, WikiMetric.objects.get(locale='es', product=p, code=L10N_TOP20_CODE).value)
        eq_(5.0, WikiMetric.objects.get(locale='es', product=p, code=L10N_TOP100_CODE).value)
        eq_(5.0, WikiMetric.objects.get(locale='es', product=p, code=L10N_ALL_CODE).value)
        eq_(5.0, WikiMetric.objects.get(locale='es', product=None, code=L10N_TOP20_CODE).value)
        eq_(5.0, WikiMetric.objects.get(locale='es', product=None, code=L10N_TOP100_CODE).value)
        eq_(5.0, WikiMetric.objects.get(locale='es', product=None, code=L10N_ALL_CODE).value)

        # Verify de metrics.
        eq_(6, WikiMetric.objects.filter(locale='de').count())
        eq_(10.0, WikiMetric.objects.get(locale='de', product=p, code=L10N_TOP20_CODE).value)
        eq_(10.0, WikiMetric.objects.get(locale='de', product=None, code=L10N_TOP100_CODE).value)
        eq_(10.0, WikiMetric.objects.get(locale='de', product=p, code=L10N_ALL_CODE).value)
        eq_(10.0, WikiMetric.objects.get(locale='de', product=None, code=L10N_TOP20_CODE).value)
        eq_(10.0, WikiMetric.objects.get(locale='de', product=None, code=L10N_TOP100_CODE).value)
        eq_(10.0, WikiMetric.objects.get(locale='de', product=None, code=L10N_ALL_CODE).value)

        # Verify ru metrics.
        eq_(6, WikiMetric.objects.filter(locale='ru').count())
        eq_(100.0, WikiMetric.objects.get(locale='ru', product=p, code=L10N_TOP20_CODE).value)
        eq_(100.0, WikiMetric.objects.get(locale='ru', product=None, code=L10N_TOP100_CODE).value)
        eq_(100.0, WikiMetric.objects.get(locale='ru', product=p, code=L10N_ALL_CODE).value)
        eq_(100.0, WikiMetric.objects.get(locale='ru', product=None, code=L10N_TOP20_CODE).value)
        eq_(100.0, WikiMetric.objects.get(locale='ru', product=None, code=L10N_TOP100_CODE).value)
        eq_(100.0, WikiMetric.objects.get(locale='ru', product=None, code=L10N_ALL_CODE).value)

        # Verify it metrics.
        eq_(6, WikiMetric.objects.filter(locale='it').count())
        eq_(0.0, WikiMetric.objects.get(locale='it', product=p, code=L10N_TOP20_CODE).value)
        eq_(0.0, WikiMetric.objects.get(locale='it', product=None, code=L10N_TOP100_CODE).value)
        eq_(0.0, WikiMetric.objects.get(locale='it', product=p, code=L10N_ALL_CODE).value)
        eq_(0.0, WikiMetric.objects.get(locale='it', product=None, code=L10N_TOP20_CODE).value)
        eq_(0.0, WikiMetric.objects.get(locale='it', product=None, code=L10N_TOP100_CODE).value)
        eq_(0.0, WikiMetric.objects.get(locale='it', product=None, code=L10N_ALL_CODE).value)

    def test_update_active_contributor_metrics(self):
        """Test the command that updates active contributor metrics."""
        day = date(2013, 7, 31)
        last_month = date(2013, 6, 15)
        start_date = date(2013, 6, 1)
        before_start = date(2013, 5, 31)

        # Create some revisions to test with:

        # 3 'en-US' contributors:
        d = DocumentFactory(locale='en-US')
        u = UserFactory()
        RevisionFactory(document=d, created=last_month, is_approved=True, reviewer=u)
        RevisionFactory(document=d, creator=u, created=last_month)

        p = ProductFactory(visible=True)
        RevisionFactory(created=start_date, document__products=[p])

        # Add two that shouldn't count:
        RevisionFactory(document=d, created=before_start)
        RevisionFactory(document=d, created=day)

        # 4 'es' contributors:
        d = DocumentFactory(locale='es')
        RevisionFactory(document=d, created=last_month, is_approved=True, reviewer=u)
        RevisionFactory(document=d, creator=u, created=last_month, reviewer=UserFactory())
        RevisionFactory(document=d, created=start_date)
        RevisionFactory(document=d, created=last_month)
        # Add two that shouldn't count:
        RevisionFactory(document=d, created=before_start)
        RevisionFactory(document=d, created=day)

        # Call the command.
        call_command('update_l10n_contributor_metrics', str(day))

        eq_(3.0, WikiMetric.objects.get(locale='en-US', product=None, date=start_date).value)
        eq_(1.0, WikiMetric.objects.get(locale='en-US', product=p, date=start_date).value)
        eq_(4.0, WikiMetric.objects.get(locale='es', product=None, date=start_date).value)
        eq_(0.0, WikiMetric.objects.get(locale='es', product=p, date=start_date).value)
