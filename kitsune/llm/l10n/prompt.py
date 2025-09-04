from typing import Any

from langchain.prompts import ChatPromptTemplate
from langchain.schema import AIMessage

from kitsune.llm.l10n.config import L10N_PROTECTED_TERMS

TRANSLATION_INSTRUCTIONS = """
# Role and task
- You are an expert at translating technical documents written in Wiki syntax about Mozilla's products from {{ source_language }} to {{ target_language }}.
- Your task is to translate the given {{ source_language }} text into {{ target_language }}, **strictly obeying** the task instructions.
- You may be given a "prior translation" as well. If so, the task instructions will describe how to use the "prior translation" to complete your task.

# Definitions
Remember the following definitions. You will use them to complete your task.

## Definition of `wiki-hook`
A `wiki-hook` is a string that case-sensitively matches the regular expression pattern that follows:

```python
r"\\[\\[(Image|Video|V|Button|UI|Include|I|Template|T):.*?\\]\\]"
```

## Definition of `wiki-article-link`
A `wiki-article-link` is a string that case-sensitively matches the regular expression pattern that follows:

```python
r"\\[\\[(?!Image:|Video:|V:|Button:|UI:|Include:|I:|Template:|T:)[^|]+?(?:\\|(?P<description>.+?))?\\]\\]"
```

## Definition of `wiki-external-link`
A `wiki-external-link` is a string that case-sensitively matches the regular expression pattern that follows:

```python
r"\\[((mailto:|git://|irc://|https?://|ftp://|/)[^<>\\]\\[\x00-\x20\x7f]*)\\s*(?P<description>.*?)\\]"
```

## Definition of `prior-translation-wiki-map`
- The `prior-translation-wiki-map` is a Python `dict` built from the "prior translation", if it is provided.
- A Python `dict` maps keys to their values.
- Each `wiki-hook`, `wiki-article-link`, and `wiki-external-link` in the {{ source_language }} text of the "prior translation" becomes a key in the `prior-translation-wiki-map`, and each key's value is its corresponding translation found in the {{ target_language }} text of the "prior translation".
- If no "prior translation" is provided, the `prior-translation-wiki-map` should be set to an empty `dict`.

# Rules for translating special strings
- Each of the following rules describes how to translate special strings that may be present within the {{ source_language }} text that you are translating.
- **Strictly obey** all of these rules when freshly translating {{ source_language }} text.

1. **Preserve unchanged** each of the following strings (each is wrapped with single backticks):
{%- for term in protected_terms %}
    - `{{ term }}`
{%- endfor %}

2. **Preserve unchanged** each string that case-sensitively matches the following regular expression:

    ```python
    r"\\{(for|key|filepath|button|menu|pref) .*?\\}"
    ```

3. For each `wiki-hook`, perform the following steps:
    - First, check if the `wiki-hook` is a key within the `prior-translation-wiki-map`.
    - If it is a key within the `prior-translation-wiki-map`, use its value from the `prior-translation-wiki-map` as its translation.
    - If it is **not** a key within the `prior-translation-wiki-map`, **preserve it unchanged**.

4. For each `wiki-article-link`, perform the following steps:
    - First, check if the `wiki-article-link` is a key within the `prior-translation-wiki-map`.
    - If it is a key within the `prior-translation-wiki-map`, use its value from the `prior-translation-wiki-map` as its translation.
    - If it is **not** a key within the `prior-translation-wiki-map`, translate only the text matched by the named group `description` (**remember to obey rule #1 above**), and **preserve the rest unchanged**.

5. For each `wiki-external-link`, perform the following steps:
    - First, check if the `wiki-external-link` is a key within the `prior-translation-wiki-map`.
    - If it is a key within the `prior-translation-wiki-map`, use its value from the `prior-translation-wiki-map` as its translation.
    - If it is **not** a key within the `prior-translation-wiki-map`, translate only the text matched by the named group `description` (**remember to obey rule #1 above**), and **preserve the rest unchanged**.

# Task Instructions
1. **Build the `prior-translation-wiki-map`**. If no "prior translation" is provided, set the `prior-translation-wiki-map` to an empty `dict`.
2. **Compare** the {{ source_language }} text you've been asked to translate with the {{ source_language }} text of the "prior translation", if provided, and **determine which parts are the same and which parts are different**. If no "prior translation" was provided, consider the entire {{ source_language }} text you've been asked to translate as different.
3. For each part that is the same, **copy** its corresponding translation from the {{ target_language }} text of the "prior translation".
4. For each part that is different, **freshly translate** that part. **Remember to obey the `Rules for translating special strings`**.
5. **Combine** the copied parts and the freshly translated parts into a final translation.
6. In your response, include your final translation and an explanation describing what you did for each step.

# Response Format
Use the following template to format your response:
<<begin-translation>>
{ translation }
<<end-translation>>
<<begin-explanation>>
{ explanation }
<<end-explanation>>
"""

SOURCE_ARTICLE = """
# Prior translation

{%if prior_translation -%}
## The {{ source_language }} text of the prior translation

```wiki
{{ prior_translation.source_text|safe }}
```

## The {{ target_language }} text of the prior translation

```wiki
{{ prior_translation.target_text|safe }}
```
{%- else -%}
There is no prior translation.
{%- endif %}

# The {{ source_language }} text to translate

```wiki
{{ source_text|safe }}
```
"""


def translation_parser(message: AIMessage) -> dict[str, Any]:
    """
    Parses the result from the LLM invocation for a translation, and returns a dictionary
    with the translation and the explanation. Special characters in the translation and
    the explanation often caused JSON decode errors when the StructuredOutputParser was
    used.
    """
    result = {}
    content = message.content
    for name in ("translation", "explanation"):
        result[name] = content.split(f"<<begin-{name}>>")[-1].split(f"<<end-{name}>>")[0].strip()
    return result


translation_prompt = ChatPromptTemplate(
    (
        ("system", TRANSLATION_INSTRUCTIONS),
        ("human", SOURCE_ARTICLE),
    ),
    template_format="jinja2",
).partial(protected_terms=L10N_PROTECTED_TERMS)
