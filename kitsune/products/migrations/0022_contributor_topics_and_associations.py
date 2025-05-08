from django.db import migrations


def create_contributor_topics_and_associations(apps, schema_editor):
    Product = apps.get_model('products', 'Product')
    Topic = apps.get_model('products', 'Topic')
    ProductTopic = apps.get_model('products', 'ProductTopic')
    Document = apps.get_model('wiki', 'Document')

    contributors_product, _ = Product.objects.get_or_create(
        slug='contributors',
        defaults={
            'title': 'Contributors',
            'description': 'For contributor tools and resources',
            'visible': False,
            'display_order': 999,
        },
    )

    templates_topic, _ = Topic.objects.get_or_create(
        slug='templates',
        defaults={
            'title': 'Templates',
            'description': 'Templates for KB articles',
            'visible': True,
            'display_order': 1,
        },
    )
    canned_topic, _ = Topic.objects.get_or_create(
        slug='canned-responses',
        defaults={
            'title': 'Canned responses',
            'description': 'Common forum responses',
            'visible': True,
            'display_order': 2,
        },
    )


    ProductTopic.objects.get_or_create(product=contributors_product, topic=templates_topic)
    ProductTopic.objects.get_or_create(product=contributors_product, topic=canned_topic)

    for doc in Document.objects.filter(is_template=True):
        doc.products.add(contributors_product)
        doc.topics.add(templates_topic)

    doc = Document.objects.filter(locale='en-US', slug='common-forum-responses').first()
    if doc:
        doc.products.add(contributors_product)
        doc.topics.add(canned_topic)


class Migration(migrations.Migration):
    dependencies = [
        ('products', '0021_auto_20241120_0218'),
        ('wiki', '0018_alter_document_restrict_to_groups'),
    ]

    operations = [
        migrations.RunPython(create_contributor_topics_and_associations, reverse_code=migrations.RunPython.noop),
    ]
