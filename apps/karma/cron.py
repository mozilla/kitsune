import cronjobs

from karma.actions import KarmaManager


@cronjobs.register
def update_top_contributors():
    """"Update the top contributor lists"""
    kmgr = KarmaManager()
    kmgr.update_top_alltime()
    kmgr.update_top_week()
