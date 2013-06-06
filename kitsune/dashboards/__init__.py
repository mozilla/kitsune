from tower import ugettext_lazy as _lazy


ACTIONS_PER_PAGE = 20
# Report time period enumerations:
LAST_7_DAYS = 0
ALL_TIME = 1
LAST_30_DAYS = 2
LAST_90_DAYS = 3
PERIODS = [(LAST_7_DAYS, _lazy(u'Last 7 days')),
           (LAST_30_DAYS, _lazy(u'Last 30 days')),
           (LAST_90_DAYS, _lazy(u'Last 90 days')),
           (ALL_TIME, _lazy(u'All Time'))]
