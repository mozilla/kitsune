from django.conf.urls import patterns, url

from kitsune.coolsearch import api

# API urls. Prefixed with /api/2/
urlpatterns = patterns(
    '',
    url('^coolsearch/search/wiki/$', api.SearchWikiView.as_view(), name='coolsearch.search_wiki'),
    url('^coolsearch/search/question/$', api.SearchQuestionView.as_view(), name='coolsearch.search_question'),
    url('^coolsearch/search/forum/$', api.SearchForumView.as_view(), name='coolsearch.search_forum'),
)
