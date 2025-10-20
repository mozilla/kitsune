from django.db import migrations, models
import django.db.models.deletion


def migrate_pinned_articles(apps, schema_editor):
    """
    Migrate the pinned articles associated with AAQConfig objects to references
    to PinnedArticleConfig objects that have been populated with those same
    pinned articles.
    """
    AAQConfig = apps.get_model("questions", "AAQConfig")
    PinnedArticleConfig = apps.get_model("wiki", "PinnedArticleConfig")

    already_created: dict[frozenset, PinnedArticleConfig] = {}

    for aaq_config in AAQConfig.objects.filter(pinned_articles__isnull=False).prefetch_related(
        "pinned_articles"
    ):
        # Create a unique and hashable signature for this set of pinned articles.
        pinned_articles = aaq_config.pinned_articles.all()
        signature = frozenset(article.id for article in pinned_articles)

        # If this same set of pinned articles hasn't already been created, create it.
        if signature not in already_created:
            title = f"Auto-migrated AAQ Set {len(already_created) + 1}"
            pinned_article_config = PinnedArticleConfig.objects.create(title=title)
            pinned_article_config.pinned_articles.set(pinned_articles)
            already_created[signature] = pinned_article_config
            print(
                f'Created PinnedArticleConfig "{title}" with {len(signature)} pinned article(s).'
            )

        aaq_config.pinned_article_config = already_created[signature]
        aaq_config.save()
        print(
            f'Associated AAQConfig "{aaq_config.title}" with PinnedArticleConfig '
            f'"{aaq_config.pinned_article_config.title}".'
        )


class Migration(migrations.Migration):
    dependencies = [
        ("wiki", "0019_pinnedarticleconfig_and_more"),
        ("questions", "0021_alter_answer_marked_as_spam_by_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="aaqconfig",
            name="pinned_article_config",
            field=models.ForeignKey(
                blank=True,
                default=None,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="aaq_configs",
                to="wiki.pinnedarticleconfig",
                verbose_name="Pinned article configuration",
            ),
        ),
        migrations.RunPython(
            migrate_pinned_articles,
            migrations.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name="aaqconfig",
            name="pinned_articles",
        ),
    ]
