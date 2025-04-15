import json

from langchain_core.messages import HumanMessage, SystemMessage

from kitsune.products.models import Product
from kitsune.questions.models import Question
from kitsune.sumo import TOPICS_BY_PRODUCT
from kitsune.wiki.config import REDIRECT_HTML
from kitsune.wiki.models import Document


def get_hierarchical_title(topic):
    result = topic.title
    while topic.parent:
        result = f"{topic.parent.title} > {result}"
        topic = topic.parent
    return result


def get_eligible_topics(product, format="json"):
    """
    Returns the available topics, as a string in the specified format,
    based on the given product.
    """
    result = dict(topics=TOPICS_BY_PRODUCT[product.title])
    return json.dumps(result, sort_keys=False, indent=2)


def get_example_questions(product, max_per_topic=20):
    """
    Returns questions and their assigned topics as a string.
    """
    topic_titles = []

    for t1 in TOPICS_BY_PRODUCT[product.title]:
        topic_titles.append(t1["title"])
        for t2 in t1.get("subtopics", ()):
            topic_titles.append(t2["title"])
            for t3 in t2.get("subtopics", ()):
                topic_titles.append(t3["title"])

    result = ["---BEGIN EXAMPLE QUESTIONS---"]

    count = 0
    for topic_title in topic_titles:
        questions = (
            Question.objects.filter(
                locale="en-US",
                is_spam=False,
                is_archived=False,
                product=product,
                topic__title=topic_title,
                moderation_timestamp__isnull=False,
            )
            .select_related("topic")
            .order_by("-num_votes_past_week")
        )

        if max_per_topic:
            questions = questions[:max_per_topic]

        for question in questions:
            count += 1
            result.append(f"---BEGIN EXAMPLE {count}---")
            result.append(f"Question: ```{question.content}```")
            result.append(f'Assigned Topic: "{get_hierarchical_title(question.topic)}"')
            result.append(f"---END EXAMPLE {count}---")

    result.append("---END EXAMPLE QUESTIONS---")
    return "\n".join(result)


def get_articles(product):
    result = []

    docs = (
        Document.objects.filter(
            locale="en-US",
            products=product,
            is_template=False,
            is_archived=False,
            parent__isnull=True,
            current_revision__isnull=False,
        )
        .exclude(html__startswith=REDIRECT_HTML)
        .select_related("current_revision")
    )

    count = 0
    for doc in docs:
        count += 1
        result.append(f"---BEGIN ARTICLE {count}---")
        result.append(doc.current_revision.content)
        result.append(f"---END ARTICLE {count}---")

    return "\n".join(result)


def get_prompt(question, include_articles=True):
    """
    Returns a list of LLM messages (a "system" message plus a "user" message) for
    use as the prompt when invoking a response from an LLM model.
    """

    if isinstance(question, tuple):
        product_title, question_content = question
        product = Product.active.get(title=product_title)
    else:
        product = question.product
        question_content = question.content

    articles = ""
    if include_articles:
        articles = (
            "Below are many articles, in Wiki syntax, that will help you better understand "
            f'Mozilla\'s "{product.title}" product:\n'
            "---BEGIN PRODUCT ARTICLES---\n"
            f"{get_articles(product)}\n"
            "---END PRODUCT ARTICLES---\n\n"
        )

    system = SystemMessage(
        (
            "You are an expert at selecting the best topic for classifying a question related"
            f' to Mozilla\'s "{product.title}" product.\n\n'
            f"{articles}"
            "Below are the hierarchical topics to select from, provided in JSON format:\n"
            "---BEGIN ELIGIBLE TOPICS---\n"
            f"{get_eligible_topics(product)}\n"
            "---END ELIGIBLE TOPICS---\n\n"
            "Given a question, consider all of the eligible topics and their descriptions,"
            " and then select the best topic. If you conclude that the question does not"
            f' relate to Mozilla\'s "{product.title}" product, or does not provide enough'
            ' information to make a selection, select the "Undefined" topic.\n'
            "Your response should be a JSON object, preceded by ```json and followed by ```,"
            " that provides the values for three keys:\n"
            '1. Your selected topic title under the key "topic". If your selected topic is a'
            " subtopic, show its hierarchy starting with its top-level topic title and"
            ' separating the topic titles with " > ".\n'
            '2. Your level of confidence ("low", "medium", "high") under the key "confidence".\n'
            '3. An explanation of why you selected the topic under the key "explanation".\n'
        )
    )

    user = HumanMessage(question_content)

    return [system, user]


def get_spam_prompt(question):
    """
    Returns a list of LLM messages (a "system" message plus a "user" message) for
    use as the prompt when invoking a response from an LLM model.
    """

    if isinstance(question, tuple):
        product_title, question_content = question
        product = Product.active.get(title=product_title)
    else:
        product = question.product
        question_content = question.content

    system = SystemMessage(
        (
            "You are an expert at determining if a question submitted by the user is spam"
            f' or not. The question should be relevant to Mozilla\'s "{product.title}" product,'
            " but sometimes it is spam.\n\n"
            "The following cases should be considered spam:\n"
            "  - It is trying to sell, advertise, or promote a product or service.\n"
            "  - It encourages users to call a phone number or contact an individual/business.\n"
            "  - It contains coupons, coupon codes, or discount codes.\n"
            "  - It contains or links to sexually explicit or pornographic content.\n"
            "  - It contains or promotes hateful, violent, racist, or abusive speech.\n"
            "  - It encourages illegal, unethical, or dangerous activities.\n"
            "  - It is trying to promote a political point of view.\n"
            "  - It is a single word or very short with no clear intent.\n"
            "  - It is impossible to determine the intent or purpose of the question.\n"
            "  - It contains an excessive amount of random symbols/emojis.\n"
            "  - It contains QR codes or images containing external links.\n"
            f'  - It is not relevant to Mozilla\'s "{product.title}" product.\n\n'
            "Given a question, determine whether or not it is spam by considering each of the"
            ' spam cases listed above. If it is spam, respond with "Spam", otherwise respond'
            ' with "Ham".'
        )
    )

    user = HumanMessage(question_content)

    return [system, user]


def get_json_result(text):
    """
    Given the text of the LLM response, extracts and returns a dict.
    """
    try:
        return json.loads(text.split("```json")[-1].split("```")[0])
    except json.JSONDecodeError as err:
        raise Exception(f"Unable to decode ({err}):\n{text}")
