from django.urls import re_path

from kitsune.wiki import kb_views

urlpatterns = [
    re_path(r"^$", kb_views.knowledge_bases, name="wiki.knowledge_bases"),
    re_path(r"^(?P<slug>[^/]+)/$", kb_views.knowledge_base, name="wiki.knowledge_base"),
]
