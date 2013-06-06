from django.core.paginator import (Paginator as DjPaginator, EmptyPage,
                                   InvalidPage, Page, PageNotAnInteger)


__all__ = ['Paginator', 'EmptyPage', 'InvalidPage']


class Paginator(DjPaginator):
    """Allows you to pass in a `count` kwarg to avoid running an
    expensive, uncacheable `SELECT COUNT` query."""

    def __init__(self, object_list, per_page,
                 orphans=0, allow_empty_first_page=True, count=None):
        super(Paginator, self).__init__(
            object_list, per_page, orphans=orphans,
            allow_empty_first_page=allow_empty_first_page)
        if count:
            self._count = count


class SimplePaginator(DjPaginator):
    """Paginator for basic Next/Previous pagination.

    The big win is that it doesn't require any COUNT queries.
    """

    def validate_number(self, number):
        """Validates the given 1-based page number.

        Override to stop checking if we have gone to far since that requires
        knowing the total number of pages.
        """
        try:
            number = int(number)
        except ValueError:
            raise PageNotAnInteger('That page number is not an integer')
        if number < 1:
            raise EmptyPage('That page number is less than 1')
        return number

    def page(self, number):
        """Returns a SimplePage object for the given 1-based page number."""
        number = self.validate_number(number)

        # Calculate the bottom (the first result).
        bottom = (number - 1) * self.per_page
        # Calculate the top, adding one so we know if there is a next page.
        top_plus_one = bottom + self.per_page + 1

        # Get the items.
        page_items = self.object_list[bottom:top_plus_one]

        # Check moved from validate_number
        if not page_items:
            if number == 1 and self.allow_empty_first_page:
                pass
            else:
                raise EmptyPage('That page contains no results')

        # Check if there is a next page.
        has_next = len(page_items) > self.per_page
        # If so, remove the extra item.
        if has_next:
            page_items = list(page_items)[:-1]

        return SimplePage(page_items, number, self, has_next)

    @property
    def _get_count(self):
        raise NotImplementedError

    @property
    def _get_num_pages(self):
        raise NotImplementedError

    @property
    def _get_page_range(self):
        raise NotImplementedError


class SimplePage(Page):
    """A page for the SimplePaginator."""
    def __init__(self, object_list, number, paginator, has_next):
        self.object_list = object_list
        self.number = number
        self.paginator = paginator
        self._has_next = has_next

    def has_next(self):
        """Is there a next page?"""
        return self._has_next

    def end_index(self):
        """Returns the 1-based index of the last object on this page."""
        return ((self.number - 1) * self.paginator.per_page +
                len(self.object_list))
