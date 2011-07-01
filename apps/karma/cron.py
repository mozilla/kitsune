import cronjobs
import waffle

from karma.actions import KarmaManager


@cronjobs.register
def update_top_contributors():
    """"Update the top contributor lists"""
    if not waffle.switch_is_active('karma'):
        return

    kmgr = KarmaManager()
    kmgr.update_top_alltime()
    kmgr.update_top_week()
