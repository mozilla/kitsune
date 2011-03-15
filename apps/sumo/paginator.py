from django.core.paginator import (Paginator as DjPaginator, EmptyPage,
                                   InvalidPage)


__all__ = ['Paginator', 'EmptyPage', 'InvalidPage']


class Paginator(DjPaginator):

    def __init__(self, object_list, per_page,
                 orphans=0, allow_empty_first_page=True, count=None):
        super(Paginator, self).__init__(
            object_list, per_page, orphans=orphans,
            allow_empty_first_page=allow_empty_first_page)
        if count:
            self._count = count
