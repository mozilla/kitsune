# -*- coding: utf-8 -*-
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_topic_in_aaq'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='image_alternate',
            field=models.ImageField(help_text='Used everywhere except the home page. Must be 96x96.', max_length=250, null=True, upload_to=b'uploads/products/', blank=True),
        ),
        migrations.AlterField(
            model_name='product',
            name='image',
            field=models.ImageField(help_text='Used on the the home page. Must be 484x244.', max_length=250, null=True, upload_to=b'uploads/products/', blank=True),
        ),
    ]
