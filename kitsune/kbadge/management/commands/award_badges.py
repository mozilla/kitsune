from datetime import date

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from kitsune.customercare import badges as aoa_badges
from kitsune.customercare.models import Reply
from kitsune.customercare.tasks import (
    maybe_award_badge as maybe_award_aoa_badge)
from kitsune.kbadge import badges  # This import hooks up email notifications # noqa
from kitsune.questions import badges as questions_badges
from kitsune.questions.models import Answer
from kitsune.questions.tasks import (
    maybe_award_badge as maybe_award_questions_badge)
from kitsune.wiki import badges as wiki_badges
from kitsune.wiki.models import Revision
from kitsune.wiki.tasks import maybe_award_badge as maybe_award_wiki_badge


class Command(BaseCommand):
    help = 'Award yearly badges starting from 2010.'

    def handle(self, *arg, **kwargs):

        for year in [2010, 2011, 2012, 2013]:

            # KB Badge
            # Figure out who the KB contributors are for the year and
            # try to award them a badge.
            user_ids = (
                Revision.objects.filter(
                    document__locale=settings.WIKI_DEFAULT_LANGUAGE,
                    created__gte=date(year, 1, 1),
                    created__lt=date(year + 1, 1, 1))
                .values_list('creator_id', flat=True)
                .distinct())

            for user in User.objects.filter(id__in=user_ids):
                if maybe_award_wiki_badge(
                        wiki_badges.WIKI_BADGES['kb-badge'], year, user):
                    print '{year} KB Badge awarded to {user}'.format(
                        year=year, user=user.username)

            # L10n Badge
            # Figure out who the L10n contributors are for the year and
            # try to award them a badge.
            user_ids = (
                Revision.objects
                .exclude(document__locale=settings.WIKI_DEFAULT_LANGUAGE)
                .filter(
                    created__gte=date(year, 1, 1),
                    created__lt=date(year + 1, 1, 1))
                .values_list('creator_id', flat=True)
                .distinct())

            for user in User.objects.filter(id__in=user_ids):
                if maybe_award_wiki_badge(
                        wiki_badges.WIKI_BADGES['l10n-badge'], year, user):
                    print '{year} L10n Badge awarded to {user}'.format(
                        year=year, user=user.username)

            # Support Forum Badge
            # Figure out who the Support Forum contributors are for the year
            # and try to award them a badge.
            user_ids = (
                Answer.objects.filter(
                    created__gte=date(year, 1, 1),
                    created__lt=date(year + 1, 1, 1))
                .values_list('creator_id', flat=True)
                .distinct())

            for user in User.objects.filter(id__in=user_ids):
                if maybe_award_questions_badge(
                        questions_badges.QUESTIONS_BADGES['answer-badge'],
                        year,
                        user):
                    print ('{year} Support Forum Badge awarded to {user}'
                           .format(year=year, user=user.username))

            # Army of Awesome Badge
            # Figure out who the Army of Awesome contributors are for the year
            # and try to award them a badge.
            user_ids = (
                Reply.objects.filter(
                    created__gte=date(year, 1, 1),
                    created__lt=date(year + 1, 1, 1))
                .values_list('user_id', flat=True)
                .distinct())

            for user in User.objects.filter(id__in=user_ids):
                if maybe_award_aoa_badge(
                        aoa_badges.AOA_BADGE, year, user):
                    print ('{year} AoA Badge awarded to {user}'
                           .format(year=year, user=user.username))
