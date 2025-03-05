from kitsune.l10n.models import MachineTranslationConfiguration


def make_mt_config(**kwargs):
    """
    Convenience function for creating a MachineTranslationConfiguration instance for testing.
    """
    mt_config = MachineTranslationConfiguration(
        llm_name="test-model", is_enabled=True, limit_to_approved_after=None
    )
    for key, value in kwargs.items():
        setattr(mt_config, key, value)
    return mt_config
