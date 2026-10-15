from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("users", "0039_remove_profile_csat_email_sent"),
    ]

    operations = [
        AddIndexConcurrently(
            model_name="profile",
            index=models.Index(
                fields=["zendesk_id"],
                condition=~models.Q(zendesk_id=""),
                name="users_profile_zendesk_id_idx",
            ),
        ),
    ]
