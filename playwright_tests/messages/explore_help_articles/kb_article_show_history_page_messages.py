class KBArticleShowHistoryPageMessages:
    PAGE_TITLE = "History of "
    DEFAULT_REVISION_FOR_LOCALE = "English"

    def get_delete_revision_endpoint(self, article_slug: str, revision_id: int) -> str:
        return f"https://support.allizom.org/en-US/kb/{article_slug}/revision/{revision_id}/delete"

    def get_remove_contributor_page_header(self, expected_username: str) -> str:
        return (f"Are you sure you want to remove {expected_username} from the document "
                f"contributors?")

    def get_contributor_added_message(self, expected_username: str) -> str:
        return f"{expected_username} added to the contributors successfully!"

    def get_contributor_removed_message(self, expected_username: str) -> str:
        return f"{expected_username} removed from the contributors successfully!"
