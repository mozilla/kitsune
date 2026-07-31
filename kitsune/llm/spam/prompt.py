from jinja2 import Template
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from kitsune.llm.prompt import ADDITIONAL_FORMAT_INSTRUCTIONS, USER_CONTENT_TEMPLATE, model_to_dict

# Must stay between LOW_ and HIGH_CONFIDENCE_THRESHOLD, so an uncertain product relevance
# judgement is routed to a human reviewer instead of being auto-actioned as spam.
UNCERTAIN_RELEVANCE_CONFIDENCE_CEILING = 70

SPAM_CRITERIA_TEMPLATE = Template("""- Attempts to sell, advertise, or promote products or services.
{% if not has_ticketing %}
- Encourages contacting phone numbers, emails, or external businesses.
{% else %}
- Encourages contacting external businesses or third-party services for support (excluding legitimate Mozilla support channels).

**Note for Zendesk tickets**: Personal information such as email addresses, account IDs, device information, order numbers, or phone numbers are expected and acceptable in support tickets. Only flag as spam if the ticket is clearly promotional, abusive, or unrelated to legitimate support needs.
{% endif %}
- Includes coupons, discount codes, or promotional offers.
- Contains or links to sexually explicit or inappropriate content.
- Contains or promotes hateful, violent, discriminatory, or abusive content.
- Encourages illegal, unethical, or dangerous behavior.
- Promotes political views or propaganda unrelated to the product.
- Is extremely short (e.g., less than 10 words), overly vague, or the primary purpose of the {{ content_name }} cannot be understood from the text.
- Its intent cannot be determined.
- Contains excessive random symbols, emojis, or gibberish text.
- Contains QR codes or links/images directing users off-site.
- Clearly unrelated to Mozilla's "{{ product }}" product features, functionality or purpose. Consult the "Judging product relevance" section before applying this criterion.""")

PRODUCT_DESCRIPTION_TEMPLATE = """
# Product description for Mozilla's "{product}" product
{description}

"""

LEGITIMATE_EXAMPLES_TEMPLATE = """
# Known-legitimate requests for Mozilla's "{product}" product
Each of the following is a genuine {content_name}, however unusual it may look. Do not classify a {content_name} as spam because it resembles one of these:
{examples}

"""

SPAM_INSTRUCTIONS = """
# Role and goal
You are a content moderation agent specialized in Mozilla's "{product}" product {content_type}.
Your task is to determine whether a user-submitted {content_name} should be classified as spam.
{product_description}{legitimate_examples}
# What Constitutes Spam?
A {content_name} is spam if **at least one** of these criteria applies:
{criteria}

# Judging product relevance
The product relevance criterion is the easiest one to misapply, so hold it to a high bar.
- Any product description above is a summary, not a complete feature list, and "{product}" gains, renames, and redesigns features in every release. A feature you cannot recall is not evidence that the feature does not exist.
- Users describe what they see in their own words rather than in official terminology. Informal, approximate, or unfamiliar names for screens, buttons, panels, and other interface elements are normal in genuine support requests.
- Apply the criterion only when the {content_name} is evidently about an altogether different subject. If it plausibly describes any part of "{product}" or its interface, however it is worded, the criterion does not apply.
- Never justify a spam classification by asserting that "{product}" lacks a feature the user describes.

# Task Instructions
Given a user {content_name} ({content_fields}), follow these steps:
1. **Evaluate carefully** against all spam criteria above.
2. **Determine classification:** If the {content_name} meets *any* of the spam criteria, classify it as spam. Otherwise, classify it as not spam.
3. Indicate your **confidence** in your classification (0-100). A higher score indicates a stronger match to the spam definitions.
   - `0` = Extremely uncertain.
   - `100` = Completely certain.
   - If the product relevance criterion is the only one that applies, and you are not certain the {content_name} is about an altogether different subject, your confidence **must not exceed {uncertain_relevance_confidence_ceiling}**, so that a person reviews it rather than it being actioned automatically.
4. Provide a concise explanation supporting your decision.
5. **Wrong product check:** Set to true only if this is a legitimate Mozilla support {content_name} for a different Mozilla product.

# Response format
{format_instructions}
"""


class SpamResult(BaseModel):
    is_spam: bool = Field(
        description="A boolean that when true indicates that the content is spam."
    )
    confidence: int = Field(
        description=(
            "An integer from 0 to 100 that indicates the level of confidence in the"
            " determination of whether or not the content is spam, with 0 representing"
            " the lowest confidence and 100 the highest."
        )
    )
    reason: str = Field(description="The reason for identifying the content as spam or not spam.")
    maybe_misclassified: bool = Field(
        description=(
            "True if this is a legitimate Mozilla support request for a different"
            ' Mozilla product. This is the result of the "wrong product check".'
        )
    )


def build_spam_prompt(product):
    """Build a spam detection prompt adapted for the product type."""
    has_ticketing = product.has_ticketing_support

    content_type = "support tickets" if has_ticketing else "support forums"
    content_name = "support ticket" if has_ticketing else "question"
    content_fields = "subject and description" if has_ticketing else "title and content"

    # Product.metadata is an unvalidated JSONField, so treat anything unexpected as absent.
    metadata = product.metadata if isinstance(product.metadata, dict) else {}

    description = metadata.get("description")
    product_description = description.strip() if isinstance(description, str) else ""
    if product_description:
        product_description = PRODUCT_DESCRIPTION_TEMPLATE.format(
            product=product.title, description=product_description
        )

    examples = metadata.get("legitimate_examples")
    if isinstance(examples, str):
        examples = [examples]
    elif not isinstance(examples, list):
        examples = []
    examples = [item.strip() for item in examples if isinstance(item, str) and item.strip()]

    legitimate_examples = ""
    if examples:
        legitimate_examples = LEGITIMATE_EXAMPLES_TEMPLATE.format(
            product=product.title,
            content_name=content_name,
            examples="\n".join(f"- {example}" for example in examples),
        )

    # Render criteria using Jinja2 template
    criteria = SPAM_CRITERIA_TEMPLATE.render(
        product=product.title, content_name=content_name, has_ticketing=has_ticketing
    )

    prompt = ChatPromptTemplate(
        (
            ("system", SPAM_INSTRUCTIONS),
            ("human", USER_CONTENT_TEMPLATE),
        )
    ).partial(
        product=product.title,
        content_type=content_type,
        content_name=content_name,
        criteria=criteria,
        content_fields=content_fields,
        product_description=product_description,
        legitimate_examples=legitimate_examples,
        uncertain_relevance_confidence_ceiling=UNCERTAIN_RELEVANCE_CONFIDENCE_CEILING,
        format_instructions=spam_pydantic_parser.get_format_instructions()
        + ADDITIONAL_FORMAT_INSTRUCTIONS,
    )

    return prompt


spam_pydantic_parser = PydanticOutputParser(pydantic_object=SpamResult)

spam_parser = spam_pydantic_parser | model_to_dict

DEFAULT_SPAM_RESULT = SpamResult(
    is_spam=False,
    confidence=0,
    maybe_misclassified=False,
    reason="Error in LLM response - defaulting to not spam",
).model_dump()
