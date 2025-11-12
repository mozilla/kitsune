from jinja2 import Template
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from kitsune.llm.prompt import ADDITIONAL_FORMAT_INSTRUCTIONS, USER_CONTENT_TEMPLATE, model_to_dict

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
- Clearly unrelated to Mozilla's "{{ product }}" product features, functionality or purpose.""")

SPAM_INSTRUCTIONS_BASE = """
# Role and goal
You are a content moderation agent specialized in Mozilla's "{product}" product {content_type}.
Your task is to determine whether a user-submitted {content_name} should be classified as spam.

# What Constitutes Spam?
A {content_name} is spam if **at least one** of these criteria applies:
{criteria}

# Task Instructions
Given a user {content_name} ({content_fields}), follow these steps:
1. **Evaluate carefully** against all spam criteria above.
2. **Determine classification:** If the {content_name} meets *any* of the spam criteria, classify it as spam. Otherwise, classify it as not spam.
3. Indicate your **confidence** in your classification (0-100). A higher score indicates a stronger match to the spam definitions.
   - `0` = Extremely uncertain.
   - `100` = Completely certain.
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

    # Render criteria using Jinja2 template
    criteria = SPAM_CRITERIA_TEMPLATE.render(
        product=product.title, content_name=content_name, has_ticketing=has_ticketing
    )

    spam_pydantic_parser = PydanticOutputParser(pydantic_object=SpamResult)
    format_instructions = (
        spam_pydantic_parser.get_format_instructions() + ADDITIONAL_FORMAT_INSTRUCTIONS
    )

    spam_instructions = SPAM_INSTRUCTIONS_BASE.format(
        product=product.title,
        content_type=content_type,
        content_name=content_name,
        criteria=criteria,
        content_fields=content_fields,
        format_instructions=format_instructions,
    )

    prompt = ChatPromptTemplate(
        (
            ("system", spam_instructions),
            ("human", USER_CONTENT_TEMPLATE),
        )
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
