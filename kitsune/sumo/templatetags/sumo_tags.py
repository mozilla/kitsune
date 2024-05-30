from django import template

from kitsune.sumo.utils import webpack_static


register = template.Library()


register.simple_tag(webpack_static)
