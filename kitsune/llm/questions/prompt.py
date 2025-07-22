from typing import Any

from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field

SPAM_INSTRUCTIONS = """
# Role and goal
You are a content moderation agent specialized in Mozilla's "{product}" product support forums.
Your task is to determine whether a user-submitted question should be classified as spam.

# What Constitutes Spam?
A question is spam if **at least one** of these criteria applies:
- Attempts to sell, advertise, or promote products or services.
- Encourages contacting phone numbers, emails, or external businesses.
- Includes coupons, discount codes, or promotional offers.
- Contains or links to sexually explicit or inappropriate content.
- Contains or promotes hateful, violent, discriminatory, or abusive content.
- Encourages illegal, unethical, or dangerous behavior.
- Promotes political views or propaganda unrelated to the product.
- Is extremely short (e.g., less than 10 words), overly vague, or the primary purpose of the question cannot be understood from the text.
- Its intent cannot be determined.
- Contains excessive random symbols, emojis, or gibberish text.
- Contains QR codes or links/images directing users off-site.
- Clearly unrelated to Mozilla's "{product}" product features, functionality or purpose.

# Task Instructions
Given a user question, follow these steps:
1. **Evaluate carefully** against all spam criteria above.
2. **Determine classification:** If the question meets *any* of the spam criteria, classify it as spam. Otherwise, classify it as not spam.
3. Indicate your **confidence** in your classification (0-100). A higher score indicates a stronger match to the spam definitions.
   - `0` = Extremely uncertain.
   - `100` = Completely certain.
4. Provide a concise explanation supporting your decision.
5. **Wrong product check:** Set to true only if this is a legitimate Mozilla support question for a different Mozilla product.

# Response format
{format_instructions}
"""

PRODUCT_INSTRUCTIONS = """
# Role and Goal
You are a specialized product reclassification agent for Mozilla's support forums.
Your task is to evaluate user-submitted questions previously flagged as spam and determine
if they should instead be reassigned to a specific Mozilla product category.

# Available Mozilla Products
You MUST select exactly one product from the following JSON-formatted list if reassignment is appropriate:
- **title**: Name of the product.
- **description**: A short description of the product.

```json
{products}
```

# When to Reassign a Question
Reassign a question to a specific product ONLY if **all** of these criteria apply:
- The question explicitly mentions or clearly relates to the product's distinctive features or functionalities.
- The question includes technical terms, error messages, or workflows unique to the specific product.
- You are highly confident the original spam classification resulted from incorrect product selection.
- The content represents a legitimate support request, not promotional or spam content.

# When NOT to Reassign
Do NOT reassign the question if **any** of these criteria apply:
- The content is genuinely promotional, spam, inappropriate, or clearly unrelated to Mozilla products.
- You cannot confidently determine the relevant Mozilla product.
- The question equally involves multiple Mozilla products with no clear primary focus.
- The original spam classification appears correct, regardless of product selection.

# Task Instructions
Given a user-submitted question previously flagged as spam, strictly follow these steps:
1. **Carefully Evaluate** whether the question clearly relates to a specific Mozilla product.
2. **Spam Verification** - Confirm explicitly that the content is not promotional or actual spam.
3. **Determine Reassignment:** If the question meets **all** reassignment criteria, explicitly select the most appropriate product. Otherwise, do not reassign.
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
Your task is to accurately classify user-submitted questions into the most appropriate topic.

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
For each question:
1. **Analyze the question** carefully to understand its primary intent or main concern.
2. **Compare against available topics** by examining each topic's:
   - Title
   - Description
   - Examples (when provided)
3. **Select exactly one topic** that best matches the question's intent, following this rule:
   - **Always prefer the most specific (lowest-level) topic that best matches the question's intent**.
   - Only select a broader (higher-level) topic if none of its lower-level topics best matches the question's intent.
4. **Default to "Undefined" if**:
   - The question is unrelated to Mozilla's "{product}".
   - The question lacks sufficient information for classification.
   - No existing topic appropriately captures the question's intent.

# Decision Criteria
- Always prioritize the primary intent of the question over secondary or minor aspects.
- Consider both explicit and implicit product features mentioned.
- Match to the most specific applicable topic when multiple topics seem relevant.
- Look for keywords that align with topic descriptions and examples.

# Response Format
{format_instructions}
"""

USER_QUESTION = """
# {subject}

{question}
"""

ADDITIONAL_FORMAT_INSTRUCTIONS = """

**Important**:
- All string values in the JSON **must** be valid JSON strings.
- **Escape any special characters** to ensure the final output is a valid JSON object. This includes, but is not limited to, double quotes (`"`), backslashes (`\\`), and control characters (e.g., `\\n`, `\\t`).
- For example, a raw string like `This is a "test".` must be formatted as `"This is a \"test\"."` or `"This is a 'test'."` in the final JSON string value.
"""


class SpamResult(BaseModel):
    is_spam: bool = Field(
        description="A boolean that when true indicates that the question is spam."
    )
    confidence: int = Field(
        description=(
            "An integer from 0 to 100 that indicates the level of confidence in the"
            " determination of whether or not the question is spam, with 0 representing"
            " the lowest confidence and 100 the highest."
        )
    )
    reason: str = Field(description="The reason for identifying the question as spam or not spam.")
    maybe_misclassified: bool = Field(
        description=(
            "True if this is a legitimate Mozilla support question for a different"
            ' Mozilla product. This is the result of the "wrong product check".'
        )
    )


class TopicResult(BaseModel):
    topic: str = Field(
        description=(
            "The title of the selected topic or subtopic. If a subtopic is selected, include"
            " only its own title — do not include the titles of any of its parent topics."
        )
    )
    reason: str = Field(description="The reason for selecting the topic.")


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


spam_pydantic_parser = PydanticOutputParser(pydantic_object=SpamResult)


topic_pydantic_parser = PydanticOutputParser(pydantic_object=TopicResult)


product_pydantic_parser = PydanticOutputParser(pydantic_object=ProductResult)


spam_prompt = ChatPromptTemplate(
    (
        ("system", SPAM_INSTRUCTIONS),
        ("human", USER_QUESTION),
    )
).partial(
    format_instructions=spam_pydantic_parser.get_format_instructions()
    + ADDITIONAL_FORMAT_INSTRUCTIONS
)


topic_prompt = ChatPromptTemplate(
    (
        ("system", TOPIC_INSTRUCTIONS),
        ("human", USER_QUESTION),
    )
).partial(
    format_instructions=topic_pydantic_parser.get_format_instructions()
    + ADDITIONAL_FORMAT_INSTRUCTIONS
)


product_prompt = ChatPromptTemplate(
    (
        ("system", PRODUCT_INSTRUCTIONS),
        ("human", USER_QUESTION),
    )
).partial(
    format_instructions=product_pydantic_parser.get_format_instructions()
    + ADDITIONAL_FORMAT_INSTRUCTIONS
)


def model_to_dict(input: BaseModel) -> dict[str, Any]:
    """
    Convert a Pydantic BaseModel instance to a dict.
    """
    return input.model_dump()


spam_parser = spam_pydantic_parser | model_to_dict


topic_parser = topic_pydantic_parser | model_to_dict


product_parser = product_pydantic_parser | model_to_dict


DEFAULT_SPAM_RESULT = SpamResult(
    is_spam=False,
    confidence=0,
    maybe_misclassified=False,
    reason="Error in LLM response - defaulting to not spam",
).model_dump()


DEFAULT_TOPIC_RESULT = TopicResult(
    topic="Undefined", reason="Error in LLM response - defaulting to 'Undefined' topic"
).model_dump()


DEFAULT_PRODUCT_RESULT = ProductResult(
    product=None,
    confidence=0,
    reason="Error in LLM response - defaulting to no product reassignment",
).model_dump()
