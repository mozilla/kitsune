class KBDashboardPageMessages:
    KB_LIVE_STATUS = "Live"
    GENERAL_NEGATIVE_STATUS = "No"
    GENERAL_POSITIVE_STATUS = "Yes"

    @staticmethod
    def get_kb_not_live_status(revision_note: str) -> str:
        return f"Review Needed: {revision_note}"
