from langchain.schema.runnable import RunnableLambda, RunnablePassthrough

from kitsune.llm.questions.prompt import spam_parser, spam_prompt, topic_parser, topic_prompt
from kitsune.llm.utils import get_llm
from kitsune.products.utils import get_taxonomy
from kitsune.questions.models import Question

DEFAULT_LLM_MODEL = "gemini-2.5-flash-preview-04-17"


def analyze_question(question: Question) -> tuple[bool, dict]:
    """
    Analyze a question from spam and classifies the topic.
    """
    llm = get_llm(model_name=DEFAULT_LLM_MODEL)

    product = question.product
    payload = {
        "question": question,
        "product": product,
        "topics": get_taxonomy(product),
    }

    spam_detection_chain = spam_prompt | llm | spam_parser
    topic_classification_chain = topic_prompt | llm | topic_parser

    pipeline = RunnablePassthrough.assign(spam_result=spam_detection_chain) | RunnableLambda(
        lambda payload: {
            **payload["spam_result"],
            **(
                {
                    "topic_result": (
                        None
                        if payload["spam_result"]["is_spam"]
                        else topic_classification_chain.invoke(payload)
                    )
                }
            ),
        }
    )
    result = pipeline.invoke(payload)
    # Draft - we need to process the result
    return result["is_spam"], result["topic_result"]
