from django.conf.urls import url

from kitsune.sumo import api


# API urls
urlpatterns = [url(r"^locales/$", api.locales_api_view, name="sumo.locales_api")]
