from django.conf.urls import patterns, url

from kitsune.inproduct import views


urlpatterns = patterns('',
    url(r'/(?P<product>[^/]+)/(?P<version>[^/]+)/(?P<platform>[^/]+)/'
        r'(?P<locale>[^/]+)(?:/(?P<topic>[^/]+))?/?',
        views.redirect, name='inproduct.redirect'),
)
