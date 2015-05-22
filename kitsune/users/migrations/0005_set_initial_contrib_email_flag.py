# -*- coding: utf-8 -*-
"""
Set the `first_{revision,question}_email_sent` flags for existing users that
have made the appropriate type of contribution. This is to avoid back filling
welcome emails to contributors.
"""
from __future__ import unicode_literals

import sys

from django.conf import settings
from django.db import migrations
from django.db.models import F

from kitsune.sumo.migrations import MigrationStatusPrinter


def contrib_email_flags_forwards(apps, schema_editor):
    Profile = apps.get_model('users', 'Profile')
    Answer = apps.get_model('questions', 'Answer')
    Revision = apps.get_model('wiki', 'Revision')

    l10n_contributor_ids = set(
        Revision.objects
        .exclude(document__locale='en-US')
        .values_list('creator', flat=True))
    (Profile.objects
        .filter(user__id__in=l10n_contributor_ids)
        .update(first_l10n_email_sent=True))

    answer_contributor_ids = set(
        Answer.objects
        .exclude(question__creator=F('creator'))
        .values_list('creator', flat=True))
    (Profile.objects
        .filter(user__id__in=answer_contributor_ids)
        .update(first_answer_email_sent=True))

    status = MigrationStatusPrinter()
    status.info('set first_l10n_email_sent on {0} profiles.', len(l10n_contributor_ids))
    status.info('set first_answer_email_sent on {0} profiles.', len(answer_contributor_ids))


def contrib_email_flags_backwards(apps, schema_editor):
    Profile = apps.get_model('users', 'Profile')
    Profile.objects.all().update(first_l10n_email_sent=False, first_answer_email_sent=False)


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_add_contrib_email_flags'),
        ('wiki', '0001_initial'),
        ('questions', '0001_initial'),
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RunPython(contrib_email_flags_forwards, contrib_email_flags_backwards),
    ]
