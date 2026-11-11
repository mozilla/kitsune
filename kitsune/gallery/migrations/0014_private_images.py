import django.db.models.deletion
from django.db import migrations, models

import kitsune.gallery.storage


def move_images_to_default_audience(apps, schema_editor):
    Audience = apps.get_model("wiki", "Audience")
    Image = apps.get_model("gallery", "Image")
    db_alias = schema_editor.connection.alias

    default = Audience.objects.using(db_alias).get(slug="default")
    Image.objects.using(db_alias).filter(audience__isnull=True).update(audience=default)


class Migration(migrations.Migration):
    dependencies = [
        ("gallery", "0013_delete_video"),
        ("wiki", "0029_knowledge_base_visibility"),
    ]

    operations = [
        migrations.AddField(
            model_name="image",
            name="audience",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="images",
                to="wiki.audience",
            ),
        ),
        migrations.RunPython(move_images_to_default_audience, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="image",
            name="audience",
            field=models.ForeignKey(
                editable=False,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="images",
                to="wiki.audience",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="image",
            unique_together={("is_draft", "creator")},
        ),
        migrations.AddConstraint(
            model_name="image",
            constraint=models.UniqueConstraint(
                fields=("locale", "title", "audience"), name="gallery_image_locale_title_audience"
            ),
        ),
        migrations.AlterField(
            model_name="image",
            name="file",
            field=models.ImageField(
                height_field="height",
                max_length=250,
                storage=kitsune.gallery.storage.gallery_storage,
                upload_to=kitsune.gallery.storage.image_upload_to,
                width_field="width",
            ),
        ),
        migrations.AlterField(
            model_name="image",
            name="thumbnail",
            field=models.ImageField(
                max_length=250,
                null=True,
                storage=kitsune.gallery.storage.gallery_storage,
                upload_to=kitsune.gallery.storage.thumbnail_upload_to,
            ),
        ),
        migrations.AddIndex(
            model_name="image",
            index=models.Index(fields=["file"], name="gallery_image_file_idx"),
        ),
        migrations.AddIndex(
            model_name="image",
            index=models.Index(fields=["thumbnail"], name="gallery_image_thumbnail_idx"),
        ),
    ]
