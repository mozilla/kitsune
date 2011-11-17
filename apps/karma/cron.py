import cronjobs
import waffle

from karma.actions import KarmaAction
from karma.models import Title


@cronjobs.register
def update_top_contributors():
    """"Update the top contributor lists and titles."""
    if not waffle.switch_is_active('karma'):
        return

    KarmaAction.objects.update_top()

    top25 = KarmaAction.objects.top_users(count=25)
    Title.objects.set_top10_contributors(top25[:10])
    Title.objects.set_top25_contributors(top25[10:25])
