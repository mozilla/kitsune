from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

from kitsune.llm.prompt import ADDITIONAL_FORMAT_INSTRUCTIONS, USER_CONTENT_TEMPLATE, model_to_dict

PRODUCT_INSTRUCTIONS = """
# Role and Goal
You are a specialized product reclassification agent for Mozilla's support.
Your task is to evaluate user-submitted content previously flagged as spam and determine
if it should instead be reassigned to a specific Mozilla product category.

# Available Mozilla Products
You MUST select exactly one product from the following JSON-formatted list if reassignment is appropriate:
- **title**: Name of the product.
- **description**: A short description of the product.

```json
{products}
```

# When to Reassign
Reassign content to a specific product ONLY if **all** of these criteria apply:
- The content explicitly mentions or clearly relates to the product's distinctive features or functionalities.
- The content includes technical terms, error messages, or workflows unique to the specific product.
- You are highly confident the original spam classification resulted from incorrect product selection.
- The content represents a legitimate support request, not promotional or spam content.

# When NOT to Reassign
Do NOT reassign the content if **any** of these criteria apply:
- The content is genuinely promotional, spam, inappropriate, or clearly unrelated to Mozilla products.
- You cannot confidently determine the relevant Mozilla product.
- The content equally involves multiple Mozilla products with no clear primary focus.
- The original spam classification appears correct, regardless of product selection.

# Task Instructions
Given user-submitted content previously flagged as spam, strictly follow these steps:
1. **Carefully Evaluate** whether the content clearly relates to a specific Mozilla product.
2. **Spam Verification** - Confirm explicitly that the content is not promotional or actual spam.
3. **Determine Reassignment:** If the content meets **all** reassignment criteria, explicitly select the most appropriate product. Otherwise, do not reassign.
4. Indicate your **confidence** in your decision (0-100), with higher scores indicating stronger certainty:
   - `0` = Extremely uncertain.
   - `100` = Completely certain.
5. Provide a concise explanation (1–2 sentences) clearly supporting your decision.

# Response Format
{format_instructions}
"""

TOPIC_INSTRUCTIONS = """
# Role and goal
You are a content classification agent specialized in Mozilla's "{product}" product support forums.
Your task is to accurately classify user-submitted content into the most appropriate topic.

# Eligible Topics
Below is a JSON-formatted list of topics you MUST choose from. Each topic includes:
- **title**: Name of the topic.
- **description**: Explanation of what the topic covers.
- **examples** (optional): Sample questions that fit clearly into the topic.
- **subtopics**: The lower-level topics, if any, of the topic.

```json
{topics}
```

# Classification Instructions
For each piece of content:
1. **Analyze the content** carefully to understand its primary intent or main concern.
2. **Compare against available topics** by examining each topic's:
   - Title
   - Description
   - Examples (when provided)
3. **Select exactly one topic** that best matches the content's intent, following this rule:
   - **Always prefer the most specific (lowest-level) topic that best matches the content's intent**.
   - Only select a broader (higher-level) topic if none of its lower-level topics best matches the content's intent.
4. **Default to "Undefined" if**:
   - The content is unrelated to Mozilla's "{product}".
   - The content lacks sufficient information for classification.
   - No existing topic appropriately captures the content's intent.

# Decision Criteria
- Always prioritize the primary intent of the content over secondary or minor aspects.
- Consider both explicit and implicit product features mentioned.
- Match to the most specific applicable topic when multiple topics seem relevant.
- Look for keywords that align with topic descriptions and examples.

# Response Format
{format_instructions}
"""


class ProductResult(BaseModel):
    product: str | None = Field(
        description=(
            "The Mozilla product selected for reassignment or null if no reassignment"
            " should be made."
        )
    )
    confidence: int = Field(
        description=(
            "An integer from 0 to 100 that indicates the level of confidence in the"
            " product reassignment decision, with 0 representing the lowest confidence"
            " and 100 the highest."
        )
    )
    reason: str = Field(
        description="The reason for reassigning to the selected product or for not reassigning."
    )


class TopicResult(BaseModel):
    topic: str = Field(
        description=(
            "The title of the selected topic or subtopic. If a subtopic is selected, include"
            " only its own title — do not include the titles of any of its parent topics."
        )
    )
    reason: str = Field(description="The reason for selecting the topic.")


# Product parser and prompt
product_pydantic_parser = PydanticOutputParser(pydantic_object=ProductResult)
product_parser = product_pydantic_parser | model_to_dict


def build_product_prompt(current_product=None):
    """Build a product classification prompt for the given product.

    Args:
        current_product: Optional Product object. If provided and slug is "mozilla-account",
            additional instructions are added for handling lockout scenarios.
    Returns:
        ChatPromptTemplate with appropriate instructions.
    """
    instructions = PRODUCT_INSTRUCTIONS

    # Add special instructions for Mozilla Accounts
    if current_product and hasattr(current_product, 'slug') and current_product.slug == "mozilla-account":
        mozilla_accounts_instructions = """

# Special Considerations for Mozilla Accounts
The current submission is for Mozilla Accounts, which handles user authentication and account management.
Users may be locked out of their accounts and may submit requests that are not actually related to Mozilla Accounts.

When evaluating submissions for Mozilla Accounts:
- **Apply stricter reassignment criteria**: Require higher confidence (minimum 80) before reassigning to a different product.
- **Explicit product mentions**: The content MUST explicitly mention specific product features, error messages, or workflows that are unique to the target product. Generic support requests are likely legitimate Mozilla Accounts issues.
- **Lockout scenarios**: Users who cannot access their accounts may submit requests about other Mozilla products thinking it will help. Only reassign if the content clearly demonstrates knowledge of the specific product's features or contains product-specific error messages.
- **When in doubt**: Do NOT reassign. It is safer to flag for manual review than to incorrectly reassign a legitimate Mozilla Accounts support request.
"""
        instructions = PRODUCT_INSTRUCTIONS + mozilla_accounts_instructions

    product_prompt = ChatPromptTemplate(
        (
            ("system", instructions),
            ("human", USER_CONTENT_TEMPLATE),
        )
    ).partial(
        format_instructions=product_pydantic_parser.get_format_instructions()
        + ADDITIONAL_FORMAT_INSTRUCTIONS
    )
    return product_prompt


# Legacy product_prompt for backward compatibility (used by existing code)
product_prompt = build_product_prompt()

DEFAULT_PRODUCT_RESULT = ProductResult(
    product=None,
    confidence=0,
    reason="Error in LLM response - defaulting to no product reassignment",
).model_dump()


# Topic parser and prompt builder
topic_pydantic_parser = PydanticOutputParser(pydantic_object=TopicResult)
topic_parser = topic_pydantic_parser | model_to_dict

DEFAULT_TOPIC_RESULT = TopicResult(
    topic="Undefined", reason="Error in LLM response - defaulting to 'Undefined' topic"
).model_dump()


def build_topic_prompt(product_title: str):
    """Build a topic classification prompt for the given product."""
    topic_prompt = ChatPromptTemplate(
        (
            ("system", TOPIC_INSTRUCTIONS.format(product=product_title)),
            ("human", USER_CONTENT_TEMPLATE),
        )
    ).partial(
        format_instructions=topic_pydantic_parser.get_format_instructions()
        + ADDITIONAL_FORMAT_INSTRUCTIONS
    )
    return topic_prompt
