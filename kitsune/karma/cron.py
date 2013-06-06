import cronjobs
import waffle

from kitsune.karma.manager import KarmaManager
from kitsune.karma.models import Title


@cronjobs.register
def update_top_contributors():
    """"Update the top contributor lists and titles."""
    if not waffle.switch_is_active('karma'):
        return

    KarmaManager().update_top()

    top25 = KarmaManager().top_users('3m', count=25)
    Title.objects.set_top10_contributors(top25[:10])
    Title.objects.set_top25_contributors(top25[10:25])
