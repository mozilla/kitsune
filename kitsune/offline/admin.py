import datetime
import logging

from django.conf import settings
from django.contrib import admin, messages
from django.shortcuts import render

from kitsune.offline.cron import build_kb_bundles
from kitsune.sumo.redis_utils import redis_client


log = logging.getLogger('k.offline')


def offline_admin(request):
    redis = redis_client('default')

    action = request.POST.get('action')
    if action == 'generate_all':
        log.info('Requested regenerating all bundles.')
        build_kb_bundles()
        messages.add_message(request, messages.SUCCESS,
                             'Bundles regenerated!')
    elif action == 'delete_all':
        if redis.delete(*redis.keys('osumo:*')):
            messages.add_message(request, messages.SUCCESS,
                                 'Deleted all bundles!')
        else:
            messages.add_message(request, messages.ERROR,
                                 'Bundle deleting failed.')

    keys = redis.keys('osumo:*')
    bundles = []
    totalsize = 0
    for key in keys:
        bundle = {}
        # reverse operation to redis_bundle_name, the schema is:
        # osumo:locale~product
        tmp = key.split(':')[1].split('~')

        locale, bundle['product'] = tuple(tmp)
        # to get the non .lower()'ed version.
        locale = settings.LANGUAGE_URL_MAP[locale]
        bundle['locale'] = settings.LOCALES[locale].english

        bundle['hash'] = redis.hget(key, 'hash')

        updated = redis.hget(key, 'updated')
        if updated is not None:
            updated = float(redis.hget(key, 'updated'))
            updated = datetime.datetime.fromtimestamp(updated)
            bundle['updated'] = updated.strftime('%Y-%m-%d %H:%M:%S')
        else:
            bundle['updated'] = 'N/A'

        bundle['size'] = round(len(redis.hget(key, 'bundle')) / 1024.0, 2)
        totalsize += bundle['size']

        bundles.append(bundle)

    # Sorting by by locale and then product
    bundles.sort(key=lambda x: x['locale'] + x['product'])

    totalsize /= 1024
    totalsize = round(totalsize, 2)

    return render(request,
                  'admin/offline.html',
                  {'title': 'Offline SUMO Administration',
                   'bundles': bundles,
                   'totalsize': totalsize})


admin.site.register_view('offline',
                         offline_admin,
                         'Offline SUMO Administration')
