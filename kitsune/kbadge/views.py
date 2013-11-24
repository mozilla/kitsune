from badger.models import Badge
from badger.views import BadgesListView


class KBadgesListView(BadgesListView):
    def get_queryset(self):
        qs = Badge.objects.order_by('-created')
        return qs

badges_list = KBadgesListView.as_view()
