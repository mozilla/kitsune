

def detect_platform_from_user_agent(request) -> list[str]:
    """
    Detect platform(s) from request.

    Returns a list of platform slugs that match the request.
    For uncertain cases, returns multiple platforms to ensure visibility.
    """
    ua = request.META.get("HTTP_USER_AGENT", "")
    if not ua:
        return ["web"]

    ua = ua.lower()

    match ua:
        case ua if "windows nt 10.0" in ua:
            return ["win10"]
        case ua if "windows nt 11.0" in ua:
            return ["win11"]
        case ua if "windows nt" in ua:
            return ["win10", "win11"]
        case ua if "mac os x" in ua or "macintosh" in ua:
            return ["mac"]
        case ua if "linux" in ua:
            return ["linux"]
        case ua if "android" in ua:
            return ["android"]
        case ua if "iphone os" in ua or "ipad os" in ua:
            return ["ios"]
        case _:
            return ["web"]
