from django.conf import settings
from elasticsearch_dsl import Search
from elasticsearch_dsl.query import Term, Terms, Bool, MultiMatch

from kitsune import search as constants
from kitsune.search.config import WIKI_DOCUMENT_INDEX_NAME, QUESTION_INDEX_NAME
from kitsune.search.documents import WikiDocumentType, QuestionDocumentType


class SimpleSearch(object):

    def __init__(self, query, doc_type, locale, product=None, with_highlights=True):
        self.query = query
        self.doc_type = doc_type
        self.locale = locale
        self.with_highlights = with_highlights
        self.product = product

    def get_queries(self):
        if self.doc_type & constants.WHERE_WIKI:
            query = WikiDocumentType.get_query(query=self.query, locale=self.locale,
                                               products=self.product)
            yield query

        if self.doc_type & constants.WHERE_SUPPORT:
            query = QuestionDocumentType.get_query(query=self.query, locale=self.locale,
                                                   products=self.product)
            yield query

    def get_indexes(self):
        if self.doc_type & constants.WHERE_WIKI:
            yield WIKI_DOCUMENT_INDEX_NAME

        if self.doc_type & constants.WHERE_SUPPORT:
            yield QUESTION_INDEX_NAME

    def get_search(self):
        highlighted_fields = ['question_content', 'document_summary']
        query = Bool(should=list(self.get_queries()))
        indexes = list(self.get_indexes())

        search = Search(index=indexes).query(query).highlight(*highlighted_fields)
        return search
