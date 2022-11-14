from django_jinja import library

from kitsune.access.utils import has_perm


library.global_function(has_perm)
