from elasticsearch_dsl import Q as DSLQ

from .tokens import BaseToken


class UnaryOperator(BaseToken):
    def __init__(self, tokens):
        self.tokens = tokens[0]
        self.argument = tokens[0][-1]

    def __repr__(self):
        return fr"{type(self).__name__}({repr(self.argument)})"


class BinaryOperator(BaseToken):
    def __init__(self, tokens):
        self.tokens = tokens[0]
        # take every other token:
        self.arguments = tokens[0][0::2]

    def __repr__(self):
        args = ", ".join([repr(x) for x in self.arguments])
        return fr"{type(self).__name__}({args})"

    def elastic_queries(self, tokens, context):
        """Get the elastic queries for every token in `tokens`."""
        return [token.elastic_query(context) for token in tokens]


class FieldOperator(UnaryOperator):
    def __repr__(self):
        return fr"FieldOperator({repr(self.argument)}, field={repr(self.tokens.field)})"

    def elastic_query(self, context):
        field = self.tokens.field
        # get field from mapping if its there
        mapping = context["settings"]["field_mappings"]
        if field in mapping:
            field = mapping[field]
        # change the the context for child tokens
        context = {
            **context,
            "fields": [field],
        }
        return self.argument.elastic_query(context)


class NotOperator(UnaryOperator):
    def elastic_query(self, context):
        return DSLQ("bool", must_not=self.argument.elastic_query(context))


class AndOperator(BinaryOperator):
    def elastic_query(self, context):
        return DSLQ("bool", must=self.elastic_queries(self.arguments, context))


class OrOperator(BinaryOperator):
    def elastic_query(self, context):
        return DSLQ(
            "bool", minimum_should_match=1, should=self.elastic_queries(self.arguments, context)
        )


class SpaceOperator(BinaryOperator):
    def elastic_query(self, context):
        query = []
        for argument in self.arguments:
            if len(query) > 0:
                # attempt to collapse adjacent tokens
                try:
                    query[-1] += argument
                except TypeError:
                    query.append(argument)
            else:
                query.append(argument)
        if len(query) == 1:
            return query[0].elastic_query(context)
        return DSLQ("bool", must=self.elastic_queries(query, context))
