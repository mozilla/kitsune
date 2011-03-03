from django.conf.urls.defaults import patterns, url

from postcrash import views


urlpatterns = patterns('',
    url('^$', views.api, name='postcrash.api'),
)
