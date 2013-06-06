from django.utils.encoding import smart_str

from kitsune.products.models import Product
from kitsune.taggit.models import Tag
from kitsune.questions.models import Question

tags_to_migrate = {
    # source tag -> product
    'desktop': ['firefox'],
    'mobile': ['mobile']
}


def assert_equals(a, b):
    assert a == b, '%s != %s' % (a, b)


def run():
    # Get all the tags to migrate.
    tags = list(Tag.objects.filter(slug__in=tags_to_migrate.keys()))

    total_affected = 0

    # For each tag, get the question and add a product for it.
    for tag in tags:
        for product_slug in tags_to_migrate[tag.slug]:
            product = Product.objects.get(slug=product_slug)

            # Assign the product to all the questions tagged with tag.
            # Pull in 5000 at a time from the db.
            n = 5000
            qs = Question.objects.filter(tags__slug=tag.slug)
            count = qs.count()
            print '%s %s questions to work on...' % (count, product_slug)
            for i in range(0, count, n):
                for question in qs[i:i + n]:
                    question.products.add(product)

                    print 'Added product "%s" to question "%s"' % (
                        smart_str(product.slug), smart_str(question.title))
                    total_affected += 1

    print 'Done! (%d)' % total_affected
