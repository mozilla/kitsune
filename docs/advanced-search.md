# Advanced Search

```eval_rst
.. contents:: :local:
```

Kitsune supports an advanced search syntax in all its search boxes.

A number of search operators and tokens,
described below,
take a `{field_name}` as an argument.
The valid field names for each of our document types are explained in the [Document Fields](#document-fields) section.

The most basic search token is simply an individual word.
For example,
the query `firefox crashes` contains two tokens `firefox` and `crashes`.

By default all simple tokens specified must exist in the same field in a document for it to be matched.
So our `firefox crashes` query will only match a document with both `firefox` _and_ `crashes` in the same field.
This behaviour can be modified using the operators below.

## Quoted Phrase

`"x y z"`

Matches the phrase,
disabling synonym matching.

e.g. `"firefox accounts"`
will match "firefox accounts" but not "firefox can't find my account".

e.g. `add-ons NOT "themes"`
will match add-ons and extensions, but not themes.

## Field Operator

`field:{field_name}:{query}`

Specifies that `{query}` should be run against `{field_name}`.
If enclosed in brackets,
`{query}` can have nested operators.

e.g. `field:keywords.en-US:(firefox NOT android)`
will find KB documents with `firefox` and without `android` in their keywords field.

### Aliases

Each document type has a number of aliases,
shown below,
which allows easy searching across document types.

e.g. using `field:title:firefox` in instant search would find both articles and questions with firefox in the title.

#### Knowledge Base Articles

```eval_rst
.. list-table::
    :header-rows: 1

    * - Alias
      - Maps To
    * - ``title``
      - ``title.{locale}``
    * - ``content``
      - ``content.{locale}``
```

#### Questions

```eval_rst
.. list-table::
    :header-rows: 1

    * - Alias
      - Maps To
    * - ``title``
      - ``question_title.{current_locale}``
    * - ``content``
      - ``question_content.{current_locale}`` or ``answer_content.{current_locale}``
    * - ``question``
      - ``question_content.{current_locale}``
    * - ``answer``
      - ``answer_content.{current_locale}``
```

#### Forum Posts

```eval_rst
.. list-table::
    :header-rows: 1

    * - Field
      - Maps To
    * - ``title``
      - ``thread_title``
```

## Boolean Operators

### NOT

`NOT x`

Specifies that the token must not exist in the document.

### AND

`x AND y`

Specifies that both tokens must exist in the document.

```eval_rst
.. note::
    A quirk of our current implementation is that ``x AND y`` can return more results than ``x y``.
    This is because ``x y`` requires both tokens to exist in the same field,
    whereas ``x AND y`` will match across fields.

    e.g. with a document like so:
    ::
        {
            "title": "x",
            "content": "y"
        }

    ``x y`` wouldn't match, but ``x AND y`` would.
```

### OR

`x OR y`

Specifies that either token must exist in the document.

## Exact Value Query

`exact:{field_name}:{value}`

Specifies that `{value}` should exactly match the value of (or token in) `{field_name}`.

e.g. `exact:question_has_solution:false` will only match questions without solutions.

### Convenience Values

These fields take a value which will be mapped to the appropriate ID internally.

#### Knowledge Base Articles

```eval_rst
.. list-table::
    :header-rows: 1

    * - Field
      - Valid values
    * - ``category``
      - ``troubleshooting``,
        ``how-to``,
        ``how-to-contribute``,
        ``navigation``
```

## Range Query

`range:{field_name}:{operator}:{value}`

Specifies that `{value}` should fall within the range of the value of `{field_name}`.
`{field_name}` must be a date or numeric field.

`{operator}` can take the following values:
* `gt` - greater than
* `gte` - greater than or equal
* `lt` - less than
* `lte` - less than or equal

`{value}` can take the following formats:
* a basic number e.g. `1`
* a date in the form `yyyy-MM-dd`
* a date and time in the form `yyyy-MM-dd'T'HH:mm:ss`
* a [date math](https://www.elastic.co/guide/en/elasticsearch/reference/current/common-options.html#date-math) value e.g. `now`, or `now-1d`

e.g. `range:question_created:gte:2021-05-27 AND range:question_created:lt:2021-05-28`
will match questions created on 27th May 2021.

e.g. `range:question_created:gte:now-2d`
will match questions created in the last two days.

## Brackets and Operator Precedence

The operators above are documented in the order they're evaluated.
To adjust the order of evaluation,
you can make use of brackets.

e.g. `NOT firefox OR crashes` will match documents which either don't have firefox in them, or have crashes in them. (This can also be expressed like `(NOT firefox) OR crashes`).

e.g. `NOT (firefox OR crashes)` will match documents which have neither firefox nor crashes in them.

## Document Fields

Fields below with a _Yes_ in the _Locale?_ column require a locale code after their field name.

e.g. to match against question content in English, you'll need to use `question_content.en-US`.

e.g. to match against answer content in German, you'll use to use `answer_content.de`.

```eval_rst
.. note::
  Currently you can't search in a locale other than the one you're using SUMO in.
  For instance, attempting to search for ``field:question_content.en-US:firefox`` on http://support.mozilla.org/de will return zero results.
```

### Knowledge Base Articles

```eval_rst
.. list-table::
    :header-rows: 1

    * - Field
      - Locale?
      - Type
    * - ``updated``
      -
      - Date
    * - ``product_ids``
      -
      - Array of Keywords
    * - ``topic_ids``
      -
      - Array of Keywords
    * - ``category``
      -
      - Keyword
    * - ``title``
      - Yes
      - Text
    * - ``content``
      - Yes
      - Text
    * - ``summary``
      - Yes
      - Text
    * - ``keywords``
      - Yes
      - Text
    * - ``slug``
      - Yes
      - Keyword
    * - ``doc_id``
      - Yes
      - Keyword
```

### Questions

```eval_rst
.. list-table::
    :header-rows: 1

    * - Field
      - Locale?
      - Type
    * - ``question_id``
      -
      - Keyword
    * - ``question_title``
      - Yes
      - Text
    * - ``question_creator_id``
      -
      - Keyword
    * - ``question_content``
      - Yes
      - Text
    * - ``question_created``
      -
      - Date
    * - ``question_updated``
      -
      - Date
    * - ``question_updated_by_id``
      -
      - Keyword
    * - ``question_has_solution``
      -
      - Boolean
    * - ``question_is_locked``
      -
      - Boolean
    * - ``question_is_archived``
      -
      - Boolean
    * - ``question_product_id``
      -
      - Keyword
    * - ``question_topic_id``
      -
      - Keyword
    * - ``question_taken_by_id``
      -
      - Keyword
    * - ``question_taken_until``
      -
      - Date
    * - ``question_tag_ids``
      -
      - Array of Keywords
    * - ``question_num_votes``
      -
      - Integer
    * - ``answer_content``
      - Yes
      - Array of Text
    * - ``locale``
      -
      - Keyword
```

### Forum Posts

```eval_rst
.. list-table::
    :header-rows: 1

    * - Field
      - Type
    * - ``thread_title``
      - Text
    * - ``thread_forum_id``
      - Keyword
    * - ``forum_slug``
      - Keyword
    * - ``thread_id``
      - Keyword
    * - ``thread_created``
      - Date
    * - ``thread_creator_id``
      - Keyword
    * - ``thread_is_locked``
      - Boolean
    * - ``thread_is_sticky``
      - Boolean
    * - ``content``
      - Text
    * - ``author_id``
      - Keyword
    * - ``created``
      - Date
    * - ``updated``
      - Date
    * - ``updated_by_id``
      - Keyword
```
