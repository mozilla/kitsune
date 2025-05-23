from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import HumanMessage
from langchain.schema.runnable import RunnableLambda

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
- Intent or relevance to Mozilla's "{product}" cannot be determined.
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

# Response format
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
3. **Select exactly one topic** that best matches the question's intent.
4. **Default to "Undefined" if**:
   - The question is unrelated to Mozilla's "{product}"
   - The question lacks sufficient information for classification
   - No existing topic appropriately captures the question's intent

# Decision Criteria
- Always prioritize the primary intent of the question over secondary or minor aspects.
- Consider both explicit and implicit product features mentioned
- Match to the most specific applicable topic when multiple topics seem relevant
- Look for keywords that align with topic descriptions and examples

# Response Format
{format_instructions}
"""

USER_QUESTION = """
# {subject}

{question}
"""


spam_parser = StructuredOutputParser.from_response_schemas(
    (
        ResponseSchema(
            name="is_spam",
            type="bool",
            description="A boolean that when true indicates that the question is spam.",
        ),
        ResponseSchema(
            name="confidence",
            type="int",
            description=(
                "An integer from 0 to 100 that indicates the level of confidence in the"
                " determination of whether or not the question is spam, with 0 representing"
                " the lowest confidence and 100 the highest."
            ),
        ),
        ResponseSchema(
            name="reason",
            type="str",
            description="The reason for identifying the question as spam or not spam.",
        ),
    )
)


topic_parser = StructuredOutputParser.from_response_schemas(
    (
        ResponseSchema(
            name="topic",
            type="str",
            description="The title of the topic selected for the question.",
        ),
        ResponseSchema(
            name="reason",
            type="str",
            description="The reason for selecting the topic.",
        ),
    )
)


spam_prompt_template = ChatPromptTemplate(
    (
        ("system", SPAM_INSTRUCTIONS),
        MessagesPlaceholder("human_message"),
    )
).partial(format_instructions=spam_parser.get_format_instructions())


topic_prompt_template = ChatPromptTemplate(
    (
        ("system", TOPIC_INSTRUCTIONS),
        MessagesPlaceholder("human_message"),
    )
).partial(format_instructions=topic_parser.get_format_instructions())


def create_human_message(payload: dict) -> dict:
    """
    Creates the human message, with the image URL's if they're present, and
    then adds it to the payload dict. Returns the modified payload dict.
    """
    content: list[dict] = [
        {
            "type": "text",
            "text": USER_QUESTION.format(**payload),
        },
    ]

    for image_url in payload.get("image_urls", ()):
        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": image_url,
                },
            }
        )

    payload["human_message"] = [HumanMessage(content=content)]
    return payload


spam_prompt = RunnableLambda(create_human_message) | spam_prompt_template


topic_prompt = RunnableLambda(create_human_message) | topic_prompt_template
