class KBDashboardPageMessages:
    KB_LIVE_STATUS = "Live"
    GENERAL_NEGATIVE_STATUS = "No"
    GENERAL_POSITIVE_STATUS = "Yes"

    def get_kb_not_live_status(self, revision_note: str) -> str:
        return f"Review Needed: {revision_note}"
