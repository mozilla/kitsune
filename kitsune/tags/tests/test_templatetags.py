from unittest.mock import Mock

from taggit.models import Tag

from kitsune.sumo.tests import TestCase
from kitsune.tags.templatetags.jinja_helpers import tags_to_text


class TestTagsToText(TestCase):
    def test_no_tags(self):
        self.assertEqual("", tags_to_text([]))

    def test_one_tag(self):
        self.assertEqual("tag1", tags_to_text([_tag("tag1")]))

    def test_two_tags(self):
        self.assertEqual("tag1,tag2", tags_to_text([_tag("tag1"), _tag("tag2")]))

    def test_three_tags(self):
        self.assertEqual(
            "tag1,tag2,tag3", tags_to_text([_tag("tag1"), _tag("tag2"), _tag("tag3")])
        )


def _tag(slug):
    tag = Mock(spec=Tag)
    tag.slug = slug
    return tag
