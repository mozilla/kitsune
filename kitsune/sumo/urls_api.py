from django.urls import re_path

from kitsune.sumo import api

# API urls
urlpatterns = [re_path(r"^locales/$", api.locales_api_view, name="sumo.locales_api")]
