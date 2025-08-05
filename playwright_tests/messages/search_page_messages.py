class SearchPageMessage:
    EMPTY_SEARCH_RESULTS_MESSAGE = ("Try searching again with a different keyword, or browse our"
                                    " featured articles below instead.")

    def expected_found_search_results_message(self, search_results_count: str,
                                              search_string: str,
                                              product_filter_option: str) -> str:
        """
        Returns the expected search results string when a search result for the searched string is
        successfully returned.

        Args:
            search_results_count (str): The expected search results counter inside the
            search message.
            search_string (str): The search string used inside the searchbar.
            product_filter_option (str): The applied product filter.
        """
        return (f"Found {search_results_count} "
                f"{'result' if search_results_count == '1' else 'results'} for ‘{search_string}’ "
                f"for ‘{product_filter_option}’")


    def expected_no_results_search_results_message(self, search_string: str,
                                                   product_filter_option: str) -> str:
        """
        Returns the expected search results string when a search result for the searched string is
        returning no search results.

        Args:
            search_string (str): The search string used inside the searchbar.
            product_filter_option (str): The applied product filter.
        """
        return f"Sorry! 0 results found for ‘{search_string}’ for ‘{product_filter_option}’"
