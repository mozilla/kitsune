from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import render
from django.utils.datastructures import SortedDict

from kitsune.announcements.models import Announcement
from kitsune.announcements.forms import AnnouncementForm
from kitsune.dashboards import ACTIONS_PER_PAGE
from kitsune.lib.sumo_locales import LOCALES
from kitsune.products.models import Product
from kitsune.sumo.utils import paginate
from kitsune.wiki.events import (
    ApproveRevisionInLocaleEvent, ReadyRevisionEvent,
    ReviewableRevisionInLocaleEvent)


def model_actions(model_class, request):
    """Returns paginated actions for the given model."""
    ct = ContentType.objects.get_for_model(model_class)
    actions = request.user.action_inbox.filter(content_type=ct)
    return paginate(request, actions, per_page=ACTIONS_PER_PAGE)


def render_readouts(request, readouts, template, locale=None, extra_data=None,
                    product=None):
    """Render a readouts, possibly with overview page.

    Use the given template, pass the template the given readouts, limit the
    considered data to the given locale, and pass along anything in the
    `extra_data` dict to the template in addition to the standard data.

    """
    current_locale = locale or request.LANGUAGE_CODE
    on_default_locale = request.LANGUAGE_CODE == settings.WIKI_DEFAULT_LANGUAGE
    data = {'readouts': SortedDict((slug, class_(request, locale=locale,
                                                 product=product))
                                   for slug, class_ in readouts.iteritems()
                                   if class_.should_show_to(request)),
            'default_locale': settings.WIKI_DEFAULT_LANGUAGE,
            'default_locale_name':
                LOCALES[settings.WIKI_DEFAULT_LANGUAGE].native,
            'current_locale': current_locale,
            'current_locale_name': LOCALES[current_locale].native,
            'request_locale_name': LOCALES[request.LANGUAGE_CODE].native,
            'is_watching_default_approved':
                ApproveRevisionInLocaleEvent.is_notifying(
                    request.user, locale=settings.WIKI_DEFAULT_LANGUAGE),
            'is_watching_other_approved':
                None if on_default_locale
                else ApproveRevisionInLocaleEvent.is_notifying(
                    request.user, locale=request.LANGUAGE_CODE),
            'is_watching_default_locale':
                ReviewableRevisionInLocaleEvent.is_notifying(
                    request.user, locale=settings.WIKI_DEFAULT_LANGUAGE),
            'is_watching_other_locale':
                None if on_default_locale
                else ReviewableRevisionInLocaleEvent.is_notifying(
                    request.user, locale=request.LANGUAGE_CODE),
            'is_watching_default_ready':
                ReadyRevisionEvent.is_notifying(request.user),
            'on_default_locale': on_default_locale,
            'announce_form': AnnouncementForm(),
            'announcements': Announcement.get_for_locale_name(current_locale),
            'product': product,
            'products': Product.objects.filter(visible=True),
        }
    if extra_data:
        data.update(extra_data)
    return render(request, 'dashboards/' + template, data)
