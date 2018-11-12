from django.conf import settings
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Term, Terms, Bool, MultiMatch

from kitsune import search as constants
from kitsune.search.config import WIKI_DOCUMENT_INDEX_NAME, QUESTION_INDEX_NAME


class SimpleSearch(object):

    def __init__(self, query, doc_type, locale, with_highlights=True):
        self.query = query
        self.doc_type = doc_type
        self.locale = locale
        self.with_highlights = with_highlights

    def get_wiki_filters(self):
        category_filter = Terms(document_category=settings.SEARCH_DEFAULT_CATEGORIES)
        locale_filter = Term(document_locale=self.locale)
        archived_filter = Term(document_is_archived=False)
        index_filter = Term(_index=WIKI_DOCUMENT_INDEX_NAME)

        return category_filter, locale_filter, archived_filter, index_filter

    def get_question_filters(self):
        archived_filter = Term(question_is_archived=False)
        helpful_filter = Term(question_has_helpful=True)
        index_filter = Term(_index=QUESTION_INDEX_NAME)
        return archived_filter, helpful_filter, index_filter

    def get_filters(self):
        filters = []
        if self.doc_type & constants.WHERE_WIKI:
            filters.append(self.get_wiki_filters())

        if self.doc_type & constants.WHERE_SUPPORT:
            filters.append(self.get_question_filters())

        return filters

    def get_wiki_query(self):
        common_fields = ['document_summary^2.0', 'document_keywords^8.0']
        match_fields = common_fields + ['document_title^6.0', 'document_content^1.0']
        match_phrase_fields = common_fields + ['document_title^10.0', 'document_content^8.0']

        match_query = MultiMatch(query=self.query, fields=match_fields)
        # Its also a multi match query, but its phrase type.
        # Which actually run phrase query among the fields.
        # https://bit.ly/2DB1qgH
        match_phrase_query = MultiMatch(query=self.query,
                                        fields=match_phrase_fields,
                                        type="phrase")

        filters = self.get_wiki_filters()
        bool_query = Bool(should=[match_query, match_phrase_query], filter=filters)
        return bool_query

    def get_question_query(self):
        all_fields = ['question_title^4.0', 'question_content^3.0', 'question_answer_content^3.0']

        match_query = MultiMatch(query=self.query, fields=all_fields)
        # Its also a multi match query, but its phrase type.
        # Which actually run phrase query among the fields.
        # https://bit.ly/2DB1qgH
        match_phrase_query = MultiMatch(query=self.query,
                                        fields=all_fields,
                                        type="phrase")

        filters = self.get_question_filters()
        bool_query = Bool(should=[match_query, match_phrase_query], filter=filters)
        return bool_query

    def get_queries(self):
        queries = []
        if self.doc_type & constants.WHERE_WIKI:
            queries.append(self.get_wiki_query())

        if self.doc_type & constants.WHERE_SUPPORT:
            queries.append(self.get_question_query())

        return Bool(should=queries)

    def get_indexes(self):
        if self.doc_type & constants.WHERE_WIKI:
            yield WIKI_DOCUMENT_INDEX_NAME

        if self.doc_type & constants.WHERE_SUPPORT:
            yield QUESTION_INDEX_NAME

    def get_search(self):
        locale_filter = Term(locale=self.locale)

        search = Search(index=list(self.get_indexes())).filter(locale_filter).query(self.get_queries())
        return search
