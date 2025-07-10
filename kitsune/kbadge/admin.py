# Pruned copy of django-badger/badger/admin.py
# https://github.com/mozilla/django-badger/blob/master/badger/admin.py

from django import forms
from django.contrib import admin
from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe

from kitsune.kbadge.models import Award, Badge


def show_image(obj):
    if not obj.image:
        return "None"
    img_url = obj.image.url
    return mark_safe(
        '<a href="{}" target="_new"><img src="{}" width="48" height="48" /></a>'.format(img_url, img_url)
    )


show_image.short_description = "Image"  # type: ignore


def build_related_link(self, model_name, name_single, name_plural, qs):
    link = "{}?{}".format(
        reverse("admin:kbadge_{}_changelist".format(model_name), args=[]),
        "badge__exact={}".format(self.id),
    )
    new_link = "{}?{}".format(
        reverse("admin:kbadge_{}_add".format(model_name), args=[]),
        "badge={}".format(self.id),
    )
    count = qs.count()
    what = ((count == 1) and name_single) or name_plural
    return '<a href="{}">{} {}</a> (<a href="{}">new</a>)'.format(link, count, what, new_link)


def related_awards_link(self):
    return mark_safe(build_related_link(self, "award", "award", "awards", self.award_set))


related_awards_link.short_description = "Awards"  # type: ignore


class BadgeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "title",
        show_image,
        "slug",
        "unique",
        "creator",
        related_awards_link,
        "created",
    )
    list_display_links = (
        "id",
        "title",
    )
    search_fields = (
        "title",
        "slug",
        "image",
        "description",
    )
    prepopulated_fields = {"slug": ("title",)}
    formfield_overrides = {
        models.ManyToManyField: {"widget": forms.widgets.SelectMultiple(attrs={"size": 25})}
    }
    # This prevents Badge from loading all the users on the site
    # which could be a very large number, take forever and result
    # in a huge page.
    raw_id_fields = ("creator",)


def badge_link(self):
    url = reverse("admin:kbadge_badge_change", args=[self.badge.id])
    return mark_safe('<a href="{}">{}</a>'.format(url, self.badge))


badge_link.short_description = "Badge"  # type: ignore


class AwardAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        badge_link,
        show_image,
        "user",
        "creator",
        "created",
    )
    fields = (
        "badge",
        "description",
        "user",
        "creator",
    )
    search_fields = ("badge__title", "badge__slug", "badge__description", "description")
    raw_id_fields = (
        "user",
        "creator",
    )


def award_link(self):
    url = reverse("admin:kbadge_award_change", args=[self.award.id])
    return mark_safe('<a href="{}">{}</a>'.format(url, self.award))


award_link.short_description = "award"  # type: ignore


for x in (
    (Badge, BadgeAdmin),
    (Award, AwardAdmin),
):
    admin.site.register(*x)
