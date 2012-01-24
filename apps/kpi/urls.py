from django.conf.urls.defaults import patterns, url, include

from tastypie.api import Api
<<<<<<< HEAD
from kpi.api import SolutionResource, ArticleVoteResource, FastResponseResource

v1_api = Api(api_name='v1')
v1_api.register(SolutionResource())
v1_api.register(ArticleVoteResource())
v1_api.register(FastResponseResource())
=======

from kpi.api import SolutionResource, VoteResource


v1_api = Api(api_name='v1')
v1_api.register(SolutionResource())
v1_api.register(VoteResource())
>>>>>>> 9f3440872088e6212a91286d769fd94efee24695


urlpatterns = patterns('kpi.views',
    url(r'^dashboard$', 'dashboard',
        name='kpi.dashboard'),
    (r'^api/', include(v1_api.urls)),

)
