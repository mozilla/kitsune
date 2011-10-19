from tags.helpers import remove_tag, tags_to_text

from mock import Mock
from nose.tools import eq_
from taggit.models import Tag

from sumo.tests import TestCase


class TestRemoveTag(TestCase):
    def setUp(self):
        self.tags = [_tag('tag1'), _tag('tag2')]

    def test_remove_tag_in_list(self):
        tag = _tag('tag3')
        self.tags.append(tag)
        tags = remove_tag(self.tags, tag)
        eq_(2, len(tags))
        assert tag not in tags

    def test_remove_tag_not_in_list(self):
        tag = _tag('tag3')
        tags = remove_tag(self.tags, tag)
        # Nothing was removed and we didn't crash.
        eq_(2, len(tags))


class TestTagsToText(TestCase):
    def test_no_tags(self):
        eq_('', tags_to_text([]))

    def test_one_tag(self):
        eq_('tag1', tags_to_text([_tag('tag1')]))

    def test_two_tags(self):
        eq_('tag1,tag2', tags_to_text([_tag('tag1'), _tag('tag2')]))

    def test_three_tags(self):
        eq_('tag1,tag2,tag3', tags_to_text([_tag('tag1'), _tag('tag2'),
                                             _tag('tag3')]))


def _tag(slug):
    tag = Mock(spec=Tag)
    tag.slug = slug
    return tag
