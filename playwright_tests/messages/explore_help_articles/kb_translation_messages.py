class KbTranslationMessages:
    LOCALIZATION_DASHBOARD_NEEDS_REVIEW_STATUS = "Necesită revizuire"
    LOCALIZATION_DASHBOARD_NEEDS_TRANSLATION_STATUS = "Necesită traducere"
    LOCALIZATION_DASHBOARD_NEEDS_ACTUALIZATION_STATUS = "Necesită actualizare"
    LOCALIZATION_DASHBOARD_TRANSLATED_STATUS = "La zi"

    def _get_kb_article_translation_ro_page(self, article_slug: str) -> str:
        return f"https://support.allizom.org/ro/kb/{article_slug}/translate"

    def get_unreviewed_localization_modified_by_text(self, username: str) -> str:
        return f"modificat de {username}"
