from datetime import datetime

from sumo.tests import TestCase
from users.tests import user
from wiki.management.commands.init_contributors import _init_contributors
from wiki.tests import revision


class InitContributorTests(TestCase):
    def test_no_approved_revisions(self):
        r = revision(save=True, is_approved=False)
        _init_contributors()
        assert not r.document.contributors.all()

    def test_one_approved_revision(self):
        r = revision(save=True, is_approved=True)
        r.document.contributors.clear()
        _init_contributors()
        assert r.creator in r.document.contributors.all()

    def test_two_approved_revision(self):
        u1 = user(save=True)
        r1 = revision(save=True, is_approved=True, creator=u1)
        d = r1.document
        u2 = user(save=True)
        revision(save=True, is_approved=True, creator=u2, document=d)
        d.contributors.clear()
        _init_contributors()
        assert u1 in d.contributors.all()
        assert u2 in d.contributors.all()

    def test_two_approved_with_rejected_and_unreviewed_between(self):
        u1 = user(save=True)
        r1 = revision(save=True, is_approved=True, creator=u1)
        d = r1.document
        u2 = user(save=True)
        revision(save=True, creator=u2, document=d)
        u3 = user(save=True)
        revision(save=True, reviewed=datetime.now(), creator=u3)
        u4 = user(save=True)
        revision(save=True, is_approved=True, creator=u4, document=d)
        d.contributors.clear()
        _init_contributors()
        assert u1 in d.contributors.all()
        assert u2 in d.contributors.all()
        assert u3 not in d.contributors.all()
        assert u4 in d.contributors.all()
