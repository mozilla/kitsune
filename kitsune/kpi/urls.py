from django.conf.urls import url

from kitsune.kpi import views


urlpatterns = [
    url(r"^dashboard$", views.dashboard, name="kpi.dashboard"),
]
