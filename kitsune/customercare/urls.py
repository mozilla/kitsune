from django.conf.urls import patterns, url


urlpatterns = patterns(
    'kitsune.customercare.views',
    url(r'^/more_tweets$', 'more_tweets', name="customercare.more_tweets"),
    url(r'^/twitter_post$', 'twitter_post', name="customercare.twitter_post"),
    url(r'^/hide_tweet$', 'hide_tweet', name="customercare.hide_tweet"),
    url(r'^$', 'landing', name='customercare.landing'),
)
