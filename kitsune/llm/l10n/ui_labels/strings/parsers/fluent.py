"""
Read Fluent files, the format of Firefox, Thunderbird and Mozilla's websites.

A Fluent string can point at other strings, and at terms. A term is a named piece
of text that isn't shown by itself, like the product's name. So a string's final
text is only known once all of an owner's files for a locale have been read.
"""

from collections.abc import Iterator

from fluent.syntax import FluentParser, FluentSerializer, ast

from kitsune.llm.l10n.ui_labels.strings.parsers.ui_string import ACCESS_KEY, UIString

MAX_DEPTH = 10
MAX_STEPS = 1000


class NotALabel(Exception):
    """The text depends on something only known when the product runs."""


class FluentFiles:
    """
    The Fluent files one owner uses in one locale.

    Strings can point at each other and at brand terms in other files, so every
    file is added before any text is read.
    """

    def __init__(self):
        self.terms: dict[str, ast.Term] = {}
        self.messages: dict[str, ast.Message] = {}
        self.entries: list[tuple[str, ast.Message]] = []
        self.parser = FluentParser(with_spans=False)

    def add(self, path: str, text: str) -> None:
        """Add a file. When two files define the same term, the one added first wins."""
        for entry in self.parser.parse(text).body:
            if isinstance(entry, ast.Term):
                self.terms.setdefault(entry.id.name, entry)
            elif isinstance(entry, ast.Message):
                self.messages.setdefault(entry.id.name, entry)
                self.entries.append((path, entry))

    def terms_text(self) -> str:
        """Return the terms as Fluent text, to add to another set of files later."""
        return FluentSerializer().serialize(ast.Resource(list(self.terms.values())))

    def strings(self) -> Iterator[UIString]:
        """Yield every text a user can see, with one entry per platform where they differ."""
        for path, message in self.entries:
            name = message.id.name
            comment = message.comment.content if message.comment else ""
            patterns = [(name, message.value)] + [
                (f"{name}.{attribute.id.name}", attribute.value)
                for attribute in message.attributes
            ]
            for key, pattern in patterns:
                if pattern is None or ACCESS_KEY.search(key):
                    continue
                try:
                    variants = list(self._variants(pattern))
                except NotALabel, ValueError:
                    continue
                for variant, text in variants:
                    yield UIString(f"{path}:{key}{variant}", text, comment)

    def _variants(self, pattern: ast.Pattern) -> Iterator[tuple[str, str]]:
        rendering = _Rendering(self)
        text = rendering.text(pattern)
        if not rendering.platforms:
            yield "", text
        for platform in sorted(rendering.platforms):
            yield f"[{platform}]", _Rendering(self, platform).text(pattern)


class _Rendering:
    """One reading of a pattern, for one platform."""

    def __init__(self, files: FluentFiles, platform: str | None = None):
        self.files = files
        self.platform = platform
        self.platforms: set[str] = set()
        self.steps = 0

    def text(
        self, pattern: ast.Pattern, arguments: dict[str, str] | None = None, depth: int = 0
    ) -> str:
        """
        `arguments` is None for a message, whose variables are only known when the
        product runs, and a dict for a term, whose variables are set by its caller.
        """
        self.steps += 1
        if depth > MAX_DEPTH or self.steps > MAX_STEPS:
            raise NotALabel
        return "".join(
            element.value
            if isinstance(element, ast.TextElement)
            else self._evaluate(element.expression, arguments, depth)
            for element in pattern.elements
        )

    def _evaluate(
        self, expression: ast.SyntaxNode, arguments: dict[str, str] | None, depth: int
    ) -> str:
        match expression:
            case ast.Placeable():
                return self._evaluate(expression.expression, arguments, depth)
            case ast.StringLiteral():
                return expression.parse()["value"]
            case ast.NumberLiteral():
                return expression.value
            case ast.MessageReference():
                return self.text(self._pattern(self.files.messages, expression), None, depth + 1)
            case ast.TermReference():
                named = expression.arguments.named if expression.arguments else []
                return self.text(
                    self._pattern(self.files.terms, expression),
                    {argument.name.name: argument.value.value for argument in named},
                    depth + 1,
                )
            case ast.VariableReference() if arguments and expression.id.name in arguments:
                return arguments[expression.id.name]
            case ast.SelectExpression():
                return self.text(self._choose(expression, arguments, depth), arguments, depth + 1)
        raise NotALabel

    def _choose(
        self, expression: ast.SelectExpression, arguments: dict[str, str] | None, depth: int
    ) -> ast.Pattern:
        names = {_name(variant.key): variant for variant in expression.variants}
        match expression.selector:
            case ast.FunctionReference(id=ast.Identifier(name="PLATFORM")):
                self.platforms.update(names)
                chosen = self.platform
            case ast.VariableReference(id=ast.Identifier(name=name)) if arguments is not None:
                chosen = arguments.get(name)
            case ast.TermReference():
                try:
                    chosen = self._evaluate(expression.selector, arguments, depth)
                except NotALabel:
                    chosen = None
            case _:
                raise NotALabel
        default = next(variant for variant in expression.variants if variant.default)
        return (names[chosen] if chosen in names else default).value

    @staticmethod
    def _pattern(
        entries: dict, reference: ast.MessageReference | ast.TermReference
    ) -> ast.Pattern:
        entry = entries.get(reference.id.name)
        if entry and reference.attribute:
            name = reference.attribute.name
            entry = next((a for a in entry.attributes if a.id.name == name), None)
        if entry is None or entry.value is None:
            raise NotALabel
        return entry.value


def _name(key: ast.Identifier | ast.NumberLiteral) -> str:
    return key.name if isinstance(key, ast.Identifier) else key.value
