from django.template import Context, Template

from notifications.tests import watch
from sumo.tests import TestCase


class Tests(TestCase):
    """Tests for our lone template tag"""

    def test_unsubscribe_instructions(self):
        """Make sure unsubscribe_instructions renders and contains the
        unsubscribe URL."""
        w = watch(save=True)
        template = Template('{% load unsubscribe_instructions %}'
                            '{% unsubscribe_instructions watch %}')
        assert w.unsubscribe_url() in template.render(Context({'watch': w}))
