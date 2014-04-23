from nose.tools import eq_

from kitsune.search.tests import synonym
from kitsune.sumo.tests import TestCase


class TestSynonymModel(TestCase):

    def test_serialize(self):
        syn = synonym(from_words="foo", to_words="bar", save=True)
        eq_(["foo => bar"], syn.serialize())
