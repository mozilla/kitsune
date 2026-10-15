import waffle

DARK_MODE_FLAG = "dark-mode"


def dark_mode_enabled(request) -> bool:
    return bool(waffle.flag_is_active(request, DARK_MODE_FLAG))
