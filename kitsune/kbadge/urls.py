from django.conf.urls import patterns, url

import badger
badger.autodiscover()


urlpatterns = patterns(
    'badger.views',

    url(r'^awards/?$', 'awards_list', name='badger.awards_list'),
    url(r'^badge/(?P<slug>[^/]+)/awards/(?P<id>\d+)/?$', 'award_detail',
        name='badger.award_detail'),
)
