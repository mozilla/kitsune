import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
        ("products", "0054_enterprise_root_and_forum_only_config"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name="SupportOrganization"),
                migrations.RemoveField(
                    model_name="productsupportconfig", name="group_default_support_type"
                ),
                migrations.RemoveField(
                    model_name="productsupportconfig", name="hybrid_support_groups"
                ),
            ],
            # Old processes still read these tables; their foreign keys would block deletes.
            database_operations=[
                migrations.AlterField(
                    model_name="supportorganization",
                    name="config",
                    field=models.ForeignKey(
                        db_constraint=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="support_organizations",
                        to="products.productsupportconfig",
                    ),
                ),
                migrations.AlterField(
                    model_name="supportorganization",
                    name="group",
                    field=models.ForeignKey(
                        db_constraint=False,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="support_organizations",
                        to="auth.group",
                    ),
                ),
                migrations.AlterField(
                    model_name="productsupportconfig",
                    name="hybrid_support_groups",
                    field=models.ManyToManyField(
                        blank=True,
                        db_constraint=False,
                        related_name="hybrid_support_configs",
                        to="auth.group",
                    ),
                ),
            ],
        ),
    ]
