from typing import Literal

from langchain_core.messages import SystemMessage

from kitsune.products.models import Product
from kitsune.products.utils import get_taxonomy


def get_system_prompt(target: Literal["spam", "topic"], product: Product) -> SystemMessage:
    """
    Returns a SystemMessage based on the given target and product.
    """
    if target == "spam":
        system_message = (
            "You are a moderation agent. Your task is to determine if a question submitted by"
            f' the user is spam. The question should be relevant to Mozilla\'s "{product.title}"'
            " product, but it may be spam.\n\n"
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
            "Given a question and its ID, determine whether or not the question is spam by"
            " considering each of the spam cases listed above. If it is spam, call the"
            " `flag_as_spam` tool with the provided question ID and your reason for"
            " classifying it as spam."
        )

    elif target == "topic":
        include_metadata = ["description", "example-questions-assigned-to-this-topic"]

        system_message = (
            "You are a classification agent. Your task is to select the best topic for"
            f' classifying a question related to Mozilla\'s "{product.title}" product.\n\n'
            "Below are the hierarchical topics to select from, provided in JSON format, where"
            f" each topic includes a title and description, as well as some example questions"
            " classified under the topic:\n"
            "---BEGIN ELIGIBLE TOPICS---\n"
            f'{get_taxonomy(product, include_metadata=include_metadata, output_format="JSON")}\n'
            "---END ELIGIBLE TOPICS---\n\n"
            "Given a question and its ID, consider the title, description, and examples of each"
            " one of the eligible topics, and then select the most relevant topic. If you"
            f' conclude that the question does not relate to Mozilla\'s "{product.title}"'
            " product, or does not provide enough information to make a selection, select the"
            ' "Undefined" topic.\n\n'
            "Once you've selected a topic, call the `assign_topic` tool with the provided"
            " question ID, the title of the selected topic, and the reason why you selected"
            " the topic."
        )

    else:
        raise ValueError(f'Unknown target "{target}".')

    return SystemMessage(system_message)
