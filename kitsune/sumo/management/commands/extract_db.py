import os

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

HEADER = """\
#######################################################################
#
# Note: This file is a generated file--do not edit it directly!
# Instead make changes to the appropriate content in the database or
# write up a bug here:
#
#     https://bugzilla.mozilla.org/enter_bug.cgi?product=support.mozilla.org
#
# with the specific lines that are problematic and why.
#
# You can generate this file by running:
#
#     ./manage.py extract_db
#
#######################################################################
"""

L10N_STRING = 'pgettext("{context}", """{id}""")\n'


def product_title_comment(product):
    comments = ["This is a product title."]

    if product.is_archived:
        comments[0] += "Archived. " + comments[0]

    if product.description:
        comments.append('The product description is "{}"'.format(product.description))

    return comments


def product_description_comment(product):
    comments = ["This is a description for the {} product.".format(product.title)]

    if product.is_archived:
        comments[0] += "Archived. " + comments[0]

    return comments


def topic_hierarchy_comment(topic):
    hierarchy = [topic]
    parent_topic = topic
    while parent_topic.parent:
        parent_topic = parent_topic.parent
        hierarchy.append(parent_topic)
    if len(hierarchy) > 1:
        return "The topic hierarcy is as follows: {}.".format(" > ".join([t.title for t in hierarchy]))
    else:
        return "The {} topic has no parent topics.".format(topic.title)


def topic_products_comment(topic):
    products = topic.products.all()
    if products.count() > 1:
        return "This topic is associated with the following products: {}.".format(
            ", ".join([p.title for p in products])
        )
    elif products.count() == 1:
        return "This topic is associated with the {} product.".format(products[0].title)
    else:
        return "This topic is not associated with any products."


def topic_title_comment(topic):
    comments = ["This is a topic title."]

    if topic.is_archived:
        comments[0] += "Archived. " + comments[0]

    comments.append(topic_hierarchy_comment(topic))

    comments.append(topic_products_comment(topic))

    if topic.description:
        comments.append('The topic description is "{}"'.format(topic.description))

    return comments


def topic_description_comment(topic):
    comments = ["This is a description for the {} topic.".format(topic.title)]

    if topic.is_archived:
        comments[0] += "Archived. " + comments[0]

    comments.append(topic_hierarchy_comment(topic))

    comments.append(topic_products_comment(topic))

    return comments


def badge_title_comment(badge):
    comments = ["This is a badge title."]

    if badge.description:
        comments.append('The badge description is "{}"'.format(badge.description))

    return comments


def badge_description_comment(badge):
    comments = ["This is a description for the {} badge.".format(badge.title)]

    return comments


class Command(BaseCommand):
    """
    Pulls strings from the database and puts them in a python file,
    wrapping each one in a gettext call.

    The models and attributes to pull are defined by DB_LOCALIZE:

    DB_LOCALIZE = {
        'some_app': {
            SomeModel': {
                'attrs': ['attr_name', 'another_attr'],
            }
        },
        'another_app': {
            AnotherModel': {
                'attrs': ['more_attrs'],
                'comments': ['Comment that will appear to localizers.'],
            }
        },
    }

    Database columns are expected to be CharFields or TextFields.
    """

    help = "Pulls strings from the database and writes them to python file."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-file",
            "-o",
            default=os.path.join(settings.ROOT, "kitsune", "sumo", "db_strings.py"),
            dest="outputfile",
            help=("The file where extracted strings are written to. " "(Default: %(default)s)"),
        )

    def handle(self, *args, **options):
        try:
            django_apps = settings.DB_LOCALIZE
        except AttributeError:
            raise CommandError("DB_LOCALIZE setting is not defined!")

        strings = []
        for app, models in list(django_apps.items()):
            for model, params in list(models.items()):
                model_class = apps.get_model(app, model)
                attrs = params["attrs"]
                qs = model_class.objects.all()
                for object in qs:
                    for attr in attrs:
                        value = getattr(object, attr)
                        if not value:
                            # Skip empty strings because empty string msgids
                            # are super bad.
                            continue
                        enforced_comments = []
                        # Enforce complex comments for certain models/attributes.
                        if app == "products":
                            if model == "Topic" and attr == "title":
                                enforced_comments = topic_title_comment(object)
                            elif model == "Topic" and attr == "description":
                                enforced_comments = topic_description_comment(object)
                            elif model == "Product" and attr == "title":
                                enforced_comments = product_title_comment(object)
                            elif model == "Product" and attr == "description":
                                enforced_comments = product_description_comment(object)
                        elif app == "kbadge":
                            if model == "Badge" and attr == "title":
                                enforced_comments = badge_title_comment(object)
                            elif model == "Badge" and attr == "description":
                                enforced_comments = badge_description_comment(object)
                        msg = {
                            "id": value,
                            "context": "DB: {}.{}.{}".format(app, model, attr),
                            "comments": enforced_comments + params.get("comments", []),
                        }
                        strings.append(msg)

        py_file = os.path.expanduser(options.get("outputfile"))
        py_file = os.path.abspath(py_file)

        print("Outputting db strings to: {filename}".format(filename=py_file))
        with open(py_file, "w+", encoding="utf-8") as f:
            f.write(HEADER)
            f.write("from django.utils.translation import pgettext\n\n")
            for s in strings:
                comments = s["comments"]
                if comments:
                    for c in comments:
                        f.write("# L10n: {comment}\n".format(comment=c))

                f.write(L10N_STRING.format(id=s["id"], context=s["context"]))
