from django.conf.urls.defaults import patterns, url, include
from tastypie.api import Api
from kpi.api import SolutionResource, ArticleVoteResource, FastResponseResource

v1_api = Api(api_name='v1')
v1_api.register(SolutionResource())
v1_api.register(ArticleVoteResource())
v1_api.register(FastResponseResource())


urlpatterns = patterns('kpi.views',
    url(r'^dashboard$', 'dashboard',
        name='kpi.dashboard'),
    (r'^api/', include(v1_api.urls)),

)
