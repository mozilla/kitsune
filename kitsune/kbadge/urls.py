from django.conf.urls import patterns, url

import badger
badger.autodiscover()

from kitsune.kbadge import views


urlpatterns = patterns(
    'badger.views',
    url(r'^$', views.badges_list, name='badger.badges_list'),
    url(r'^awards/?$', 'awards_list', name='badger.awards_list'),
    url(r'^badge/(?P<slug>[^/]+)/awards/(?P<id>\d+)/?$', 'award_detail',
        name='badger.award_detail'),
    url(r'^badge/(?P<slug>[^/]+)/?$', 'detail',
        name='badger.detail'),
)
