

def detect_platform_from_user_agent(request) -> list[str]:
    """
    Detect platform(s) from request using Client Hints first, then fallback to User Agent.
    Returns a list of platform slugs that match the request.
    For uncertain cases, returns multiple platforms to ensure visibility.
    """
    # Check for JavaScript override first (for AJAX requests)
    js_platform = request.META.get('_JS_PLATFORM')
    if js_platform:
        return [js_platform]

    platform = request.META.get("HTTP_SEC_CH_UA_PLATFORM", "").strip('"').lower()
    platform_version = request.META.get("HTTP_SEC_CH_UA_PLATFORM_VERSION", "").strip('"')
    ua = request.META.get("HTTP_USER_AGENT", "").lower()

    PLATFORM_MAP = {
        "windows": (["win10", "win11"], ["windows nt"]),
        "macos": (["mac"], ["mac os x", "macintosh"]),
        "linux": (["linux"], ["linux"]),
        "android": (["android"], ["android"]),
        "ios": (["mac"], ["iphone os", "ipad os"]),  # Map iOS to mac for now
    }

    if platform == "windows" and platform_version:
        try:
            major_version = int(platform_version.split('.')[0])
            if major_version >= 13:
                return ["win11"]
            elif major_version >= 10:
                return ["win10"]
            else:
                return ["win10", "win11"]
        except (ValueError, IndexError):
            pass

    if platform in PLATFORM_MAP:
        return PLATFORM_MAP[platform][0]

    if ua:
        for hint_name, (result, ua_patterns) in PLATFORM_MAP.items():
            if any(pattern in ua for pattern in ua_patterns):
                return result
    return ["web"]
