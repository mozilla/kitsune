from django.conf.urls import url

from kitsune.customercare import views


urlpatterns = [
    url(r"^/moderate$", views.moderate, name="customercare.moderate"),
    url(r"^/more_tweets$", views.more_tweets, name="customercare.more_tweets"),
    url(r"^/twitter_post$", views.twitter_post, name="customercare.twitter_post"),
    url(r"^/hide_tweet$", views.hide_tweet, name="customercare.hide_tweet"),
    url(r"^$", views.landing, name="customercare.landing"),
]
