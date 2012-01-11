from django.utils.datastructures import SortedDict

from tower import ugettext_lazy as _lazy


MARKETPLACE_CATEGORIES = SortedDict([
    ('payments', _lazy('Payments')),
    ('applications', _lazy('Applications')),
    ('account', _lazy('Account')),
])
