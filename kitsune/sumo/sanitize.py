"""Centralized HTML sanitization utilities wrapping justhtml.

This module provides reusable wrappers around justhtml for all sanitization
patterns used across the kitsune codebase.
"""

import re
from collections.abc import Collection, Mapping

from justhtml import (
    Decide,
    JustHTML,
    Linkify,
    RewriteAttrs,
    SanitizationPolicy,
    SetAttrs,
    UrlPolicy,
    UrlRule,
)

# Private imports: justhtml doesn't re-export these. Staying in sync with
# upstream matters here — if the validation tightens in a future release,
# mirrored regexes would silently go stale and reintroduce the serializer
# ValueError.
from justhtml.serialize import _SERIALIZABLE_ATTR_NAME_RE, _SERIALIZABLE_TAG_NAME_RE


def _drop_unserializable_attrs(element):
    """Strip attributes whose names justhtml's serializer would reject.

    justhtml's HTML5 tokenizer is permissive about what it accepts and
    will happily produce attribute names containing characters its own
    serializer then refuses to emit, causing a `ValueError` at write
    time. This callback compares each attribute name against the same
    regex the serializer uses and drops anything that wouldn't survive
    serialization.

    Example:
        Input: `<a href="x" ba\\d="y" onmo\\use="z">`
        Output: `<a href="x">`  (malformed attr names removed, element
        kept, valid attrs preserved)

    Returning `None` signals "no change" to justhtml, avoiding a
    rewrite when everything is already valid.
    """
    cleaned = {k: v for k, v in element.attrs.items() if _SERIALIZABLE_ATTR_NAME_RE.match(k)}
    if len(cleaned) != len(element.attrs):
        return cleaned
    return None


def _decide_unserializable_tags(node):
    """Unwrap elements whose tag names justhtml's serializer would reject.

    The HTML5 tokenizer treats any `<word` sequence as a start tag and
    will produce element names from characters the serializer then
    refuses to emit (anything outside `[A-Za-z][A-Za-z0-9:_-]*`). Rather
    than letting the serializer raise, this callback asks justhtml to
    `UNWRAP` such elements: the wrapper is removed but its children —
    text and any valid descendants — stay in place, so the user's
    content survives.

    Examples:
        Input: `<p>see <foo.bar>details</foo.bar> here</p>`
        Output: `<p>see details here</p>`

        Input: `<baz)>text</baz)>`
        Output: `text`

    Non-element nodes (text, comments, and the document/fragment
    containers whose names start with `#`) are always kept as-is.
    """
    name = node.name
    if name.startswith("#"):
        return Decide.KEEP
    if not _SERIALIZABLE_TAG_NAME_RE.match(name):
        return Decide.UNWRAP
    return Decide.KEEP


RESTRICTED_HTML_TAGS = {
    "a",
    "abbr",
    "acronym",
    "b",
    "blockquote",
    "br",
    "code",
    "em",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "hr",
    "i",
    "li",
    "ol",
    "pre",
    "strong",
    "table",
    "tbody",
    "td",
    "tfoot",
    "th",
    "thead",
    "tr",
    "u",
    "ul",
    "p",
}
RESTRICTED_HTML_ATTRIBUTES = {
    "a": ["href", "title", "rel"],
    "abbr": ["title"],
    "acronym": ["title"],
    "td": ["colspan", "rowspan"],
    "th": ["colspan", "rowspan", "scope"],
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
    transforms = [
        Decide("*", _decide_unserializable_tags),
        RewriteAttrs("*", _drop_unserializable_attrs),
        Linkify(),
    ]
    if nofollow:
        transforms.append(SetAttrs("a", rel="nofollow"))
    return JustHTML(text, fragment=True, sanitize=False, transforms=transforms).to_html(
        pretty=False
    )
