import logging

# from elasticutils.contrib.django import Indexable, MappingType

log = logging.getLogger("k.search.es")


class SearchMixin(object):
    """A mixin which adds ES indexing support for the model

    When using this mixin, make sure to implement:

    * get_mapping_type

    Additionally, after defining your model, remember to register it and any
    related models which affect it::

         register_for_indexing(MyModel, 'some_app')
         register_for_indexing(RelatedModel, 'some_app',
                                instance_to_indexee=lambda r: r.my_model)

    """

    @classmethod
    def get_mapping_type(cls):
        """Return the MappingType for this model"""
        ...

    def index_later(self):
        """Register myself to be indexed at the end of the request."""
        return

    def unindex_later(self):
        """Register myself to be unindexed at the end of the request."""
        return


class SearchMappingType(object):
    """Contains helpers on top of what ElasticUtils provides

    Subclasses should implement the following:

    1. get_mapping needs to return {'properties': { ... fields ... }}
    2. get_query_fields should return a list of fields for query
    3. extract_document
    4. get_model
    5. the mapping type class should be decorated with
       ``@register_mapping_type``

    Then make sure to:

    6. implement get_mapping_type on the related model

    """

    list_keys: list[str] = []
    seconds_ago_filter = None

    @classmethod
    def search(cls):
        ...

    @classmethod
    def get_index(cls):
        ...

    @classmethod
    def get_index_group(cls):
        ...

    @classmethod
    def get_query_fields(cls):
        """Return the list of fields for query"""
        ...

    @classmethod
    def get_localized_fields(cls):
        ...

    @classmethod
    def get_indexable(cls, seconds_ago=0):
        ...

    @classmethod
    def reshape(cls, results):
        ...

    @classmethod
    def index(cls, *args, **kwargs):
        ...

    @classmethod
    def unindex(cls, *args, **kwargs):
        ...

    @classmethod
    def morelikethis(cls, id_, s, fields):
        """MoreLikeThis API"""
        ...


# class RecordManager(models.Manager):
#     def outstanding(self):
#         """Return outstanding records"""
#         return self.filter(status__in=Record.STATUS_OUTSTANDING)


# class Record(ModelBase):
#     """Indexing record."""

#     STATUS_NEW = 0
#     STATUS_IN_PROGRESS = 1
#     STATUS_FAIL = 2
#     STATUS_SUCCESS = 3

#     STATUS_CHOICES = (
#         (STATUS_NEW, "new"),
#         (STATUS_IN_PROGRESS, "in progress"),
#         (STATUS_FAIL, "done - fail"),
#         (STATUS_SUCCESS, "done - success"),
#     )

#     STATUS_OUTSTANDING = [STATUS_NEW, STATUS_IN_PROGRESS]

#     batch_id = models.CharField(max_length=10)
#     name = models.CharField(max_length=255)
#     creation_time = models.DateTimeField(auto_now_add=True)
#     start_time = models.DateTimeField(null=True)
#     end_time = models.DateTimeField(null=True)
#     status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_NEW)
#     message = models.CharField(max_length=255, blank=True)

#     objects = RecordManager()

#     class Meta:
#         ordering = ["-start_time"]
#         permissions = (("reindex", "Can run a full reindexing"),)

#     def delta(self):
#         """Return the timedelta."""
#         if self.start_time and self.end_time:
#             return self.end_time - self.start_time
#         return None

#     def _complete(self, status, msg="Done"):
#         self.end_time = datetime.datetime.now()
#         self.status = status
#         self.message = msg

#     def mark_fail(self, msg):
#         """Mark as failed.

#         :arg msg: the error message it failed with

#         """
#         self._complete(self.STATUS_FAIL, msg[:255])
#         self.save()

#     def mark_success(self, msg="Success"):
#         """Mark as succeeded.

#         :arg msg: success message if any

#         """
#         self._complete(self.STATUS_SUCCESS, msg[:255])
#         self.save()

#     def __str__(self):
#         return "%s:%s%s" % (self.batch_id, self.name, self.status)


# class Synonym(ModelBase):
#     """To be serialized into ES for synonyms."""

#     from_words = models.CharField(max_length=1024)
#     to_words = models.CharField(max_length=1024)

#     def __str__(self):
#         return "{0} => {1}".format(self.from_words, self.to_words)
