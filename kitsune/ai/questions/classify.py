from kitsune.ai.llms import get_llm
from kitsune.ai.questions.prompt import spam_parser, spam_prompt
from kitsune.ai.questions.prompt import topic_parser, topic_prompt
from kitsune.ai.questions.utils import assign_topic, flag_as_spam
from kitsune.products.utils import get_taxonomy
from kitsune.questions.models import Question


def classify(question: Question, model_name: str = "gemini-2.5-flash-preview-04-17") -> None:
    """
    Determines whether or not to classify a question as spam, and if not, assigns a topic
    to the question.
    """
    model = get_llm(model_name)

    spam_chain = spam_prompt | model | spam_parser
    topic_chain = topic_prompt | model | topic_parser

    spam_result = spam_chain.invoke(
        dict(
            question=question.content,
            product=question.product.title,
            format_instructions=spam_parser.get_format_instructions(only_json=True),
        )
    )

    print(f"\nspam_result = {spam_result}")

    if spam_result.get("is_spam"):
        flag_as_spam(question, spam_result["reason"])
    else:
        topic_result = topic_chain.invoke(
            dict(
                question=question.content,
                product=question.product.title,
                topics=get_taxonomy(
                    question.product,
                    include_metadata=["description", "examples"],
                    output_format="JSON",
                ),
                format_instructions=topic_parser.get_format_instructions(only_json=True),
            )
        )
        assign_topic(question, topic_result["topic"], topic_result["reason"])

        print(f"\ntopic_result = {topic_result}")
