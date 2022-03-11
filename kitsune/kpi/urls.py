from django.urls import re_path

from kitsune.kpi import views

urlpatterns = [
    re_path(r"^dashboard$", views.dashboard, name="kpi.dashboard"),
]
