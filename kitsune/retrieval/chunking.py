"""Scope-aware chunking for stored Kitsune content.

Each ``data-for`` attribute is retained as one opaque clause in an outer-to-inner scope path. Exact
repeated clauses are collapsed because ``A and A`` is still ``A``. Otherwise, the path preserves
the difference between a comma-separated clause and nested clauses without deciding how selectors
should be matched at query time. A nested projection includes unconditional text and its
ancestor-scope text from the same content block, keeping the instruction context a browser reader
would see.

We project only scope paths observed in the content. We deliberately do not synthesize the
Cartesian product of independent reader configurations; that retrieval policy belongs to the
retriever, not the chunker.
"""

import re
from dataclasses import dataclass

from lxml import html as lxml_html

__all__ = ["Chunk", "ShowForScope", "chunk", "chunk_kb", "count_tokens", "parse_data_for"]

HEADING_TAGS = ("h1", "h2", "h3")
CONTAINER_TAGS = ("div", "section")
MAX_TOKENS = 512
OVERLAP_TOKENS = 64
_SEGMENT_BOUNDARY = re.compile(r"(\n+|(?<=[.!?])\s+)")

# Each item is one element's selector clause; tuple order represents DOM nesting (logical AND).
type ShowForScope = tuple[frozenset[str], ...]


@dataclass(frozen=True)
class Chunk:
    text: str
    position: int
    heading_path: str
    # One clause per nested show-for element, ordered outermost to innermost.
    scope: ShowForScope = ()

    @property
    def applies_to(self) -> frozenset[str]:
        """Flat selector metadata retained for the current Elasticsearch contract.

        ``scope`` remains authoritative: flattening is intentionally deferred until this boundary
        so chunk projection does not lose comma-versus-nesting semantics.
        """
        return frozenset(selector for clause in self.scope for selector in clause)


@dataclass(frozen=True)
class Fragment:
    text: str
    scope: ShowForScope
    # synthetic layout glue (cell/row/item separators); not real content
    layout: bool = False


@dataclass(frozen=True)
class Heading:
    level: int
    ordinal: int
    fragments: tuple[Fragment, ...]


@dataclass(frozen=True)
class Block:
    headings: tuple[Heading, ...]
    fragments: tuple[Fragment, ...]
    whitespace: str = "normal"


def parse_data_for(value: str) -> frozenset[str]:
    """Parse the selectors in one ``data-for`` clause without interpreting them."""
    return frozenset(token.strip() for token in value.split(",") if token.strip())


def count_tokens(text: str) -> int:
    return len(text) // 4


def _is_showfor(element) -> bool:
    return "for" in (element.get("class") or "").split()


def _element_scope(element, parent_scope: ShowForScope) -> ShowForScope:
    if not _is_showfor(element):
        return parent_scope
    clause = parse_data_for(element.get("data-for", ""))
    # Repeating an identical condition through nested parser wrappers adds no reader constraint.
    return (*parent_scope, clause) if clause and clause not in parent_scope else parent_scope


def _whitespace(element) -> str:
    if element.tag in ("ol", "ul", "table"):
        return "lines"
    return "pre" if element.tag == "pre" else "normal"


def _fragments(element, parent_scope: ShowForScope) -> list[Fragment]:
    """Flatten a DOM subtree into ordered, scope-tagged fragments."""
    scope = _element_scope(element, parent_scope)
    if element.tag in ("ol", "ul"):
        return _list_fragments(element, scope)
    if element.tag == "table":
        return _table_fragments(element, scope)

    frags: list[Fragment] = []
    if element.text:
        frags.append(Fragment(element.text, scope))
    for child in element:
        if child.tag == "br":
            frags.append(Fragment("\n", scope, layout=True))
        else:
            frags.extend(_fragments(child, scope))
        # a tail belongs to the parent, not to a conditional child
        if child.tail:
            frags.append(Fragment(child.tail, scope))
    return frags


def _list_fragments(element, scope: ShowForScope) -> list[Fragment]:
    frags: list[Fragment] = []
    items = [child for child in element if child.tag == "li"]
    for index, item in enumerate(items):
        frags.extend(_fragments(item, scope))
        if index < len(items) - 1:
            frags.append(Fragment("\n", scope, layout=True))
    return frags


def _table_fragments(element, scope: ShowForScope) -> list[Fragment]:
    rows = [[cell for cell in row if cell.tag in ("td", "th")] for row in element.iter("tr")]
    rows = [cells for cells in rows if cells]
    frags: list[Fragment] = []
    for row_index, cells in enumerate(rows):
        for cell_index, cell in enumerate(cells):
            frags.extend(_fragments(cell, scope))
            if cell_index < len(cells) - 1:
                frags.append(Fragment(" | ", scope, layout=True))
        if row_index < len(rows) - 1:
            frags.append(Fragment("\n", scope, layout=True))
    return frags


def _render_fragments(
    fragments: tuple[Fragment, ...], signature: ShowForScope, whitespace: str = "normal"
) -> str:
    """Render one observed scope path.

    A fragment is visible when its scope is a prefix of the target signature. The empty scope is
    therefore unconditional, while outer-scope text is inherited by each nested projection.
    Structural glue (layout separators and, outside ``pre``, whitespace-only fragments) is kept
    only between two included content fragments.
    """
    parts: list[str] = []
    pending: list[str] = []
    for fragment in fragments:
        if fragment.scope != signature[: len(fragment.scope)]:
            continue
        # glue must not anchor a pending separator; in pre, whitespace is real content
        if fragment.layout or (whitespace != "pre" and not fragment.text.strip()):
            if parts:
                pending.append(fragment.text)
        else:
            parts.extend(pending)
            pending = []
            parts.append(fragment.text)
    text = "".join(parts)
    if whitespace == "pre":
        return text.strip()
    if whitespace == "lines":
        return "\n".join(
            normalized for line in text.splitlines() if (normalized := " ".join(line.split()))
        )
    return " ".join(text.split())


def _content_scopes(fragments: tuple[Fragment, ...]) -> list[ShowForScope]:
    scopes: list[ShowForScope] = []
    for fragment in fragments:
        if fragment.layout or not (fragment.text.strip() and fragment.scope):
            continue
        if fragment.scope not in scopes:
            scopes.append(fragment.scope)
    return scopes


def _atomize(text: str, max_tokens: int) -> list[str]:
    """Split text into atoms within max_tokens, each carrying its trailing separator so a plain
    concatenation preserves newlines and indentation. Splits on line/sentence boundaries, then
    words, then characters for anything still too large."""
    atoms: list[str] = []
    parts = _SEGMENT_BOUNDARY.split(text)
    for index in range(0, len(parts), 2):
        segment = parts[index]
        delimiter = parts[index + 1] if index + 1 < len(parts) else ""
        if not segment:
            if delimiter and atoms:
                atoms[-1] += delimiter
            continue
        if count_tokens(segment + delimiter) <= max_tokens:
            atoms.append(segment + delimiter)
            continue
        words = segment.split()
        for offset, word in enumerate(words):
            tail = delimiter if offset == len(words) - 1 else " "
            if count_tokens(word) <= max_tokens:
                atoms.append(word + tail)
                continue
            limit = max_tokens * 4
            for start in range(0, len(word), limit):
                chunk_ = word[start : start + limit]
                atoms.append(chunk_ + (tail if start + limit >= len(word) else ""))
    return atoms


def _split_oversized(text: str, max_tokens: int) -> list[str]:
    if count_tokens(text) <= max_tokens:
        return [text]

    pieces: list[str] = []
    current: list[str] = []
    for atom in _atomize(text, max_tokens):
        if current and count_tokens("".join([*current, atom])) > max_tokens:
            pieces.append("".join(current))
            # carry a trailing overlap into the next piece for continuity across the seam
            overlap: list[str] = []
            for previous in reversed(current):
                if overlap and count_tokens("".join([previous, *overlap])) > OVERLAP_TOKENS:
                    break
                overlap.insert(0, previous)
            # drop the overlap if it leaves no room for the atom that triggered the split
            current = overlap if count_tokens("".join([*overlap, atom])) <= max_tokens else []
        current.append(atom)
    if current:
        pieces.append("".join(current))
    return pieces


def chunk_kb(html: str, *, title: str) -> list[Chunk]:
    container = lxml_html.fragment_fromstring(html, create_parent="div")

    # Phase 1 — walk the DOM into heading-aware blocks of scope-tagged fragments.
    blocks: list[Block] = []
    heading_stack: list[Heading] = []
    heading_ordinal = 0

    def add_text_block(text: str | None, scope: ShowForScope) -> None:
        if text and text.strip():
            blocks.append(Block(tuple(heading_stack), (Fragment(text, scope),)))

    def walk(element, scope: ShowForScope) -> None:
        nonlocal heading_ordinal

        add_text_block(element.text, scope)
        for child in element:
            if child.tag in HEADING_TAGS:
                level = int(child.tag[1])
                while heading_stack and heading_stack[-1].level >= level:
                    heading_stack.pop()
                heading_ordinal += 1
                heading_stack.append(
                    Heading(level, heading_ordinal, tuple(_fragments(child, scope)))
                )
            elif _is_showfor(child):
                # a direct show-for wrapper (any tag: expand_fors emits both <div> and <span>)
                saved_headings = list(heading_stack)
                walk(child, _element_scope(child, scope))
                heading_stack[:] = saved_headings  # conditional headings don't leak past the block
            elif child.tag in CONTAINER_TAGS:
                walk(child, scope)
            else:
                fragments = tuple(_fragments(child, scope))
                if any(fragment.text.strip() for fragment in fragments):
                    blocks.append(Block(tuple(heading_stack), fragments, _whitespace(child)))
            add_text_block(child.tail, scope)

    walk(container, ())

    # Phase 2 — project each block into one passage per observed scope signature.
    projections: list[tuple[tuple[int, ...], str, ShowForScope, str]] = []
    for block in blocks:
        section = tuple(heading.ordinal for heading in block.headings)
        has_unconditional_body = any(
            fragment.text.strip() and not fragment.scope and not fragment.layout
            for fragment in block.fragments
        )
        signatures: list[ShowForScope] = [()] if has_unconditional_body else []
        signatures.extend(_content_scopes(block.fragments))
        if has_unconditional_body:
            for heading in block.headings:
                for scope in _content_scopes(heading.fragments):
                    if scope not in signatures:
                        signatures.append(scope)

        for signature in signatures:
            text = _render_fragments(block.fragments, signature, block.whitespace)
            if text:
                heading_parts = [title]
                for heading in block.headings:
                    if heading_text := _render_fragments(heading.fragments, signature):
                        heading_parts.append(heading_text)
                projections.append((section, " > ".join(heading_parts), signature, text))

    # Phase 3 — group co-located passages, then size-split into chunks.
    groups: dict[tuple[tuple[int, ...], str, ShowForScope], list[str]] = {}
    for section, path, signature, text in projections:
        groups.setdefault((section, path, signature), []).append(text)

    chunks: list[Chunk] = []
    for (_, path, signature), texts in groups.items():
        prefix = f"{path}\n"
        budget = MAX_TOKENS - count_tokens(prefix) - 1
        for piece in _split_oversized(" ".join(texts), budget):
            chunks.append(
                Chunk(
                    text=prefix + piece,
                    position=len(chunks),
                    heading_path=path,
                    scope=signature,
                )
            )
    return chunks


def chunk(content_type: str, html: str, *, title: str) -> list[Chunk]:
    if content_type == "kb":
        return chunk_kb(html, title=title)
    raise ValueError(f"Unsupported content_type: {content_type!r}")
