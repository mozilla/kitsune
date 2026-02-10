"""Centralized HTML sanitization utilities wrapping justhtml.

This module provides reusable wrappers around justhtml for all sanitization
patterns used across the kitsune codebase.
"""

import re
from collections.abc import Collection, Mapping

from justhtml import JustHTML, Linkify, SanitizationPolicy, SetAttrs, UrlPolicy, UrlRule

ALLOWED_BIO_TAGS = {
    "a",
    "abbr",
    "acronym",
    "b",
    "blockquote",
    "code",
    "em",
    "i",
    "li",
    "ol",
    "strong",
    "ul",
    "p",
}
ALLOWED_BIO_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
    "abbr": ["title"],
    "acronym": ["title"],
}

URL_LIKE_ATTRS = frozenset(
    (
        "href",
        "src",
        "srcset",
        "poster",
        "action",
        "formaction",
        "data",
        "cite",
        "background",
        "ping",
    )
)


def build_url_policy(allowed_attributes: Mapping[str, Collection[str]]) -> UrlPolicy:
    """Build a permissive `UrlPolicy` from an allowed-attributes mapping.

    justhtml requires explicit `(tag, attr)` rules for URL-bearing
    attributes (e.g. `href`, `src`). Without a rule, the attribute
    is stripped regardless of the allowlist. This function scans
    *allowed_attributes* for any URL-like attributes and creates a rule
    for each one, allowing relative URLs and common schemes (http,
    https, mailto, tel, ftp). This matches bleach's default behavior
    of not filtering URLs.

    Wildcard (`"*"`) entries are skipped because justhtml URL rules
    require a concrete tag name.

    Args:
        allowed_attributes: Mapping of tag names to allowed attribute
            names, e.g. `{"a": ["href", "title"], "img": ["src"]}`.
    """
    rules = {}
    for tag, attrs in allowed_attributes.items():
        if tag == "*":
            continue
        for attr in attrs:
            if (attr in URL_LIKE_ATTRS) and ((tag, attr) not in rules):
                # Permissive rule matching bleach's behavior (allow all schemes, relative URLs).
                rules[(tag, attr)] = UrlRule(
                    allow_relative=True,
                    allowed_schemes={"http", "https", "mailto", "tel", "ftp"},
                )
    return UrlPolicy(default_handling="allow", allow_rules=rules)


def clean(
    html: str,
    tags: Collection[str] = (),
    attributes: Mapping[str, Collection[str]] | None = None,
    css_properties: Collection[str] | None = None,
    strip: bool = True,
) -> str:
    """Sanitize HTML, keeping only the specified tags and attributes.

    Disallowed tags are handled according to the `strip` parameter:
    - strip=True (default): tags are removed but their text content is kept.
      `clean("<b>hi</b>")` → `"hi"`
    - strip=False: tags are escaped as visible text.
      `clean("<b>hi</b>", strip=False)` → `"&lt;b&gt;hi&lt;/b&gt;"`

    HTML comments are always stripped.

    Args:
        html: The HTML string to sanitize.
        tags: Iterable of allowed tag names. Defaults to `()` (strip all).
        attributes: Mapping of tag names to allowed attribute lists,
            e.g. `{"a": ["href", "title"]}`. Supports `"*"` for
            attributes allowed on all tags.
        css_properties: Optional set of allowed CSS property names.
            When provided, `style` attributes are preserved and filtered
            to only these properties.
        strip: How to handle disallowed tags. `True` removes them
            (keeping content), `False` escapes them as visible text.
    """
    attrs_dict = dict(attributes) if attributes else {}

    policy_kwargs = {
        "allowed_tags": tags,
        "allowed_attributes": attrs_dict,
        "url_policy": build_url_policy(attrs_dict),
        "disallowed_tag_handling": "unwrap" if strip else "escape",
    }
    if css_properties:
        policy_kwargs["allowed_css_properties"] = css_properties

    policy = SanitizationPolicy(**policy_kwargs)

    if policy.disallowed_tag_handling == "escape":
        # Workaround: justhtml's "escape" mode doesn't respect drop_comments=True,
        # escaping comments instead of dropping them. Strip them before sanitizing.
        html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)

    return JustHTML(html, fragment=True, policy=policy).to_html(pretty=False)


def linkify(text: str, nofollow: bool = False) -> str:
    """Convert plain-text URLs into clickable `<a>` links.

    Existing HTML is preserved as-is (no sanitization is performed).
    Only bare URLs in text content are wrapped in anchor tags.

    Args:
        text: HTML string to scan for plain-text URLs.
        nofollow: If `True`, adds `rel="nofollow"` to every
            generated link.
    """
    transforms = [Linkify()]
    if nofollow:
        transforms.append(SetAttrs("a", rel="nofollow"))
    return JustHTML(text, fragment=True, sanitize=False, transforms=transforms).to_html(
        pretty=False
    )
