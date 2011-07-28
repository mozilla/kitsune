import cronjobs
import waffle

from karma.actions import KarmaAction


@cronjobs.register
def update_top_contributors():
    """"Update the top contributor lists"""
    if not waffle.switch_is_active('karma'):
        return

    KarmaAction.objects.update_top_alltime()
    KarmaAction.objects.update_top_week()
