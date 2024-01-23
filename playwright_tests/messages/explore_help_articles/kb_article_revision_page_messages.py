class KBArticleRevision:
    KB_ARTICLE_REVISION_HEADER = "Review Revision of "
    UNREVIEWED_REVISION_HEADER = " Unreviewed Revision: "
    KB_ARTICLE_REVISION_NO_CURRENT_REV_TEXT = "This document does not have a current revision."
    KB_ARTICLE_REVISION_KEYWORD_HEADER = "Keywords:"

    def get_kb_article_revision_details(self,
                                        revision_id: str,
                                        username: str,
                                        revision_comment: str) -> str:
        return (f"Reviewing Revision {revision_id} by {username}. Back to HistoryRevision Comment:"
                f" {revision_comment}")

    def get_unreviewed_revision_details(self,
                                        revision_id: str,
                                        username: str,
                                        revision_comment: str) -> str:
        return (f"Revision {revision_id} by {username}. Revision Comment: {revision_comment}Review"
                f" Revision {revision_id}")
