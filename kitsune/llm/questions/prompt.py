from langchain.output_parsers import ResponseSchema, StructuredOutputParser
from langchain.prompts import ChatPromptTemplate


SPAM_INSTRUCTIONS = """
# Role and goal
- You are a moderation agent, and an expert on Mozilla's "{product}" product.
- Your goal is to determine if the given question is spam.
- The question should be relevant to Mozilla's "{product}" product, but it may be spam.

# Spam cases
In each of the following cases, the question should be considered spam:
  - It is trying to sell, advertise, or promote a product or service.
  - It encourages users to call a phone number or contact an individual/business.
  - It contains coupons, coupon codes, or discount codes.
  - It contains or links to sexually explicit or pornographic content.
  - It contains or promotes hateful, violent, racist, or abusive speech.
  - It encourages illegal, unethical, or dangerous activities.
  - It is trying to promote a political point of view.
  - It is a single word or very short with no clear intent.
  - It is impossible to determine the intent or purpose of the question.
  - It contains an excessive amount of random symbols/emojis.
  - It contains QR codes or images containing external links.
  - It is not relevant to Mozilla's "{product}" product.

# Specific instructions
Given a question, you must do the following:
- Determine whether or not the question is spam by considering each of the spam cases
  listed above.
- Provide a reason for your determination.

# Response format instructions
{format_instructions}
"""

TOPIC_INSTRUCTIONS = """
# Role and goal
- You are a classification agent, and an expert on Mozilla's "{product}" product.
- Your goal is to select the best topic for classifying a question about Mozilla's
  "{product}" product.

# Eligible Topics
Below are the hierarchical topics you MUST select from, provided in JSON format. Each
topic includes a title and a description, and may also include some examples that will
help you identify the kinds of questions which should be classified under that topic:

```json
{topics}
```

# Specific instructions
- Given a question, consider the title, description, and examples of each one of the
  eligible topics listed above, and then select the most relevant topic.
- If you conclude that the question does not relate to Mozilla's "{product}" product,
  or does not provide enough information to make a selection, select the "Undefined" topic.
- Provide a reason for your selection.

# Response format instructions
{format_instructions}
"""


spam_parser = StructuredOutputParser.from_response_schemas(
    (
        ResponseSchema(
            name="is_spam",
            type="bool",
            description="A boolean that when true indicates that the question is spam.",
        ),
        ResponseSchema(
            name="reason",
            type="string",
            description="The reason for identifying the question as spam or not spam.",
        ),
    )
)


topic_parser = StructuredOutputParser.from_response_schemas(
    (
        ResponseSchema(
            name="topic",
            type="string",
            description="The topic selected for the question.",
        ),
        ResponseSchema(
            name="reason",
            type="string",
            description="The reason for selecting the topic.",
        ),
    )
)


spam_prompt = ChatPromptTemplate((("system", SPAM_INSTRUCTIONS), ("human", "{question}")))


topic_prompt = ChatPromptTemplate((("system", TOPIC_INSTRUCTIONS), ("human", "{question}")))
