# Generated by Django 4.1.10 on 2023-09-06 16:34

from django.db import migrations, models
import django.db.models.functions.text


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_squashed_0027_profile_zendesk_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="profile",
            name="bio",
            field=models.TextField(
                blank=True,
                help_text="Some HTML supported: &#x3C;abbr title&#x3E; &#x3C;blockquote&#x3E; &#x3C;code&#x3E; &#x3C;em&#x3E; &#x3C;i&#x3E; &#x3C;li&#x3E; &#x3C;ol&#x3E; &#x3C;strong&#x3E; &#x3C;ul&#x3E;. Links are forbidden.",
                null=True,
                verbose_name="Biography",
            ),
        ),
        migrations.AddIndex(
            model_name="profile",
            index=models.Index(
                django.db.models.functions.text.Upper("name"), name="upper_name_idx"
            ),
        ),
    ]
