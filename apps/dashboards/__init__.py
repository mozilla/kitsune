from tower import ugettext_lazy as _lazy


ACTIONS_PER_PAGE = 20
# Report time period enumerations:
THIS_WEEK = 0
ALL_TIME = 1
PERIODS = [(THIS_WEEK, _lazy(u'This Week')),
           (ALL_TIME, _lazy(u'All Time'))]
