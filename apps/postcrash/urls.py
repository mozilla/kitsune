from django.conf.urls import patterns, url

from postcrash import views


urlpatterns = patterns('',
    url('^$', views.api, name='postcrash.api'),
)
