from django.utils.translation import ugettext_lazy as _lazy


WHERE_WIKI = 1
WHERE_SUPPORT = 2
WHERE_BASIC = WHERE_WIKI | WHERE_SUPPORT
WHERE_DISCUSSION = 4

INTERVAL_NONE = 0
INTERVAL_BEFORE = 1
INTERVAL_AFTER = 2

DATE_LIST = (
    (INTERVAL_NONE, _lazy("Don't filter")),
    (INTERVAL_BEFORE, _lazy("Before")),
    (INTERVAL_AFTER, _lazy("After")),
)

# For discussion forums
# Integer values here map to tuples from SORT defined above
SORTBY_FORUMS = (
    (0, _lazy("Relevance")),
    (1, _lazy("Last post date")),
    (2, _lazy("Original post date")),
    (3, _lazy("Number of replies")),
)

DISCUSSION_STICKY = 1
DISCUSSION_LOCKED = 2

DISCUSSION_STATUS_LIST = (
    (DISCUSSION_STICKY, _lazy("Sticky")),
    (DISCUSSION_LOCKED, _lazy("Locked")),
)

# For support questions
TERNARY_OFF = 0
TERNARY_YES = 1
TERNARY_NO = -1

TERNARY_LIST = (
    (TERNARY_OFF, _lazy("Don't filter")),
    (TERNARY_YES, _lazy("Yes")),
    (TERNARY_NO, _lazy("No")),
)

NUMBER_LIST = (
    (INTERVAL_NONE, _lazy("Don't filter")),
    (INTERVAL_BEFORE, _lazy("Less than")),
    (INTERVAL_AFTER, _lazy("More than")),
)

SORT_QUESTIONS = (
    ("-_score", "-updated"),  # default
    ("-updated",),
    ("-created",),
    ("-question_num_answers",),
)

SORTBY_QUESTIONS = (
    (0, _lazy("Relevance")),
    (1, _lazy("Last answer date")),
    (2, _lazy("Question date")),
    (3, _lazy("Number of answers")),
)


SORT_DOCUMENTS = {
    "relevance": ("-_score",),
    "helpful": ("-document_recent_helpful_votes",),
}

SORTBY_DOCUMENTS_CHOICES = (
    ("relevance", _lazy("Relevance")),
    ("helpful", _lazy("Helpful votes")),
)

HIGHLIGHT_TAG = "strong"
SNIPPET_LENGTH = 500

NO_MATCH = _lazy("No pages matched the search criteria")
