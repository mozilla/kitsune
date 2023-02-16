# 2 - Storing localized content in Search

Date: 2020-10-27

## Status

Pending

## Context

Kitsune supports many locales,
and has content which we want to be searchable in those locales.

Elasticsearch has support for many language-specific analyzers:
https://www.elastic.co/guide/en/elasticsearch/reference/7.9/analysis-lang-analyzer.html

Search v1 used per-document analyzers,
that is to say, within the same index:

```
doc_1: { "content": "Hello world" }
doc_2: { "content": "Hallo Welt" }
```

`doc_1.content` could be analyzed using an english analyzer,
and `doc_2.content` could be analyzed using a german analyzer.

Well before version 7 ES removed this feature,
and now all fields of the same name across an index must be analyzed the same,
so we must take a different approach with the current Search implementation.

We can either place separate locales in their own index,
and set up locale-specific analyzers for the same field name across indices.
Or we can keep separate locales within the same index,
and define unique field names for each field which needs to be analyzed under a specific locale.

## Decision

Heavily influenced by: https://www.elastic.co/blog/multilingual-search-using-language-identification-in-elasticsearch

We will store all documents within the same index and use an Object field for fields which need to use locale-specific analyzers.

We will call this field `SumoLocaleAwareTextField` and will have a key for each locale,
with the appropriate analyzer defined on that key,
such that:

```
doc_1: { "content": { "en-US": "Hello world" }}
doc_2: { "content": { "de": "Hallo Welt" }}
```

`doc_1.content.en-US` is analyzed using an english analyzer,
and `doc_2.content.de` is analyzed using a german analyzer.

## Consequences

We won't need to manage many indeces of wildly different sizes,
as we would if we used one index per locale.

Documents within a specific locale can be searched for by searching on the `field.locale-name` field,
for instance `content.en-US`.

Searching across all locales can be performed with a wildcard (like `content.*`).
