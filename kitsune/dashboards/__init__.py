from django.utils.translation import gettext_lazy as _lazy

# Report time period enumerations:
LAST_7_DAYS = 0
LAST_YEAR = 1
LAST_30_DAYS = 2
LAST_90_DAYS = 3
PERIODS = [
    (LAST_7_DAYS, _lazy("Last 7 days")),
    (LAST_30_DAYS, _lazy("Last 30 days")),
    (LAST_90_DAYS, _lazy("Last 90 days")),
    (LAST_YEAR, _lazy("Last Year")),
]
