import re
from typing import Any

from langchain.prompts import ChatPromptTemplate
from langchain.schema import AIMessage
from langchain_core.exceptions import OutputParserException

from kitsune.llm.l10n.config import L10N_PROTECTED_TERMS

DELIMITER = "<<<<translation-and-explanation-delimiter>>>>"
TRANSLATION_PARSER_REGEX = re.compile(
    rf"^(```wiki\s+)?\s*(?P<translation>.+?)(?(1)\s*```)\s*{DELIMITER}\s*(?P<explanation>.+)$",
    re.DOTALL,
)

TRANSLATION_INSTRUCTIONS = """
# Role and task
- You are an expert at translating technical documents written in Wiki syntax about Mozilla's products from {{ source_language }} to {{ target_language }}.
- However, the definitions, rules, and task instructions provided below **take precedence over everything else**.
- Your task is to translate the given {{ source_language }} text into {{ target_language }}, **strictly following** the definitions, rules, and task instructions provided below.
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
r"\\[((mailto:|git://|irc://|https?://|ftp://|/)[^<>\\]\\[\\x00-\\x20\\x7f]*)\\s*(?P<description>.*?)\\]"
```

## Definition of `wiki-ui-element`
A `wiki-ui-element` is a string that case-sensitively matches the regular expression pattern that follows:

```python
r"\\{(button|menu|pref) [^}]*\\}"
```

## Definition of `prior-translation-wiki-map`
- The `prior-translation-wiki-map` is a Python `dict` built from the "prior translation", if it is provided.
- A Python `dict` maps keys to their values.
- **IMPORTANT**: Extract **ALL** `wiki-hook`, `wiki-article-link`, `wiki-external-link`, and `wiki-ui-element` elements from the **ENTIRE** {{ source_language }} text of the "prior translation". Each element becomes a key in the `prior-translation-wiki-map`, and each key's value is its corresponding translation found in the {{ target_language }} text of the "prior translation".
- This `prior-translation-wiki-map` preserves human-localized wiki elements, which **must be reused** whenever those elements appear anywhere in your translation, regardless of whether they appear in changed or unchanged sections.
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
    r"\\{(for|key|filepath) [^}]*\\}"
    ```

    - In other words, preserve unchanged both the tags and the text inside the tags.
    - For example, each of the strings `{for win10}` and `{key Ctrl+T}` and `{filepath file}` should be preserved unchanged.

3. **CRITICAL RULE**: For **every** wiki element (`wiki-hook`, `wiki-article-link`, `wiki-external-link`, or `wiki-ui-element`) you encounter **anywhere** in the text (whether in same or different parts), you **MUST** perform the following steps in order:
    - **FIRST**: Check if the element exists as a key within the `prior-translation-wiki-map`.
    - **If found in the map**: Use its value from the `prior-translation-wiki-map` as its translation. This preserves human localization. **Do NOT translate it freshly**.
    - **ONLY if NOT found in the map**:
        - For `wiki-hook` and `wiki-ui-element`: **preserve it unchanged**
        - For `wiki-article-link` and `wiki-external-link`: translate only the `description` text if present (**remember to obey rule #1 above**), and **preserve the rest unchanged**. If there is no `description`, preserve the entire element unchanged.
    - **NEVER** translate a wiki element freshly if it exists in the `prior-translation-wiki-map`. Always prefer the map value.

# Task Instructions
1. **Build the `prior-translation-wiki-map`**:
   - If a "prior translation" is provided, extract **ALL** wiki elements (`wiki-hook`, `wiki-article-link`, `wiki-external-link`, and `wiki-ui-element`) from the **ENTIRE** {{ source_language }} text of the "prior translation" and map each to its corresponding translation in the {{ target_language }} text.
   - This map must include wiki elements from **both** the unchanged AND changed sections of the prior translation.
   - If no "prior translation" is provided, set the `prior-translation-wiki-map` to an empty `dict`.
2. **Compare** the {{ source_language }} text you've been asked to translate with the {{ source_language }} text of the "prior translation", if provided, and **determine which parts are the same and which parts are different**. If no "prior translation" was provided, consider the entire {{ source_language }} text you've been asked to translate as different.
3. For each part that is the same, **copy** its corresponding translation from the {{ target_language }} text of the "prior translation".
4. For each part that is different, **freshly translate** that part:
   - **Remember to obey ALL of the `Rules for translating special strings`**.
   - **CRITICAL**: Even in different/changed parts, you **MUST** check the `prior-translation-wiki-map` for every wiki element (per Rule #3) before translating. This ensures already-localized wiki elements are preserved.
   - Only translate text that is not covered by the protection rules. Wiki elements found in the map must use their map values.
5. **Combine** the copied parts and the freshly translated parts into a final translation.
6. In your response, include your final translation and an explanation describing what you did for each step.
7. **Format** your response by providing your final translation, followed by the delimiter `{{ delimiter }}`, followed by your explanation. Your final translation **must be provided without any added commentary, formatting, markdown fences, or extra text of any kind**.
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
    content = message.text()

    mo = TRANSLATION_PARSER_REGEX.match(content)

    if not mo:
        raise OutputParserException(
            "The LLM response was not formatted correctly.",
            observation="The response was not formatted correctly.",
            llm_output=content,
        )

    result["translation"] = mo.group("translation")
    result["explanation"] = mo.group("explanation")
    return result


translation_prompt = ChatPromptTemplate(
    (
        ("system", TRANSLATION_INSTRUCTIONS),
        ("human", SOURCE_ARTICLE),
    ),
    template_format="jinja2",
).partial(protected_terms=L10N_PROTECTED_TERMS, delimiter=DELIMITER)
