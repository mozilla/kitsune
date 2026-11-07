from django.db import migrations
from django.db.models import Case, Value, When

# Same fallbacks as NON_SUPPORTED_LOCALES in settings.
FALLBACKS = {
    "bm": "fr",
    "ee": "en-US",
    "ha": "en-US",
    "ig": "en-US",
    "ln": "fr",
    "mg": "fr",
    "ta-LK": "ta",
    "tn": "en-US",
    "yo": "en-US",
    "zu": "en-US",
}


def forward(apps, schema_editor):
    Profile = apps.get_model("users", "Profile")
    # One update, so the large profile table is only read once.
    Profile.objects.filter(locale__in=FALLBACKS).update(
        locale=Case(*[When(locale=old, then=Value(new)) for old, new in FALLBACKS.items()])
    )


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0040_profile_zendesk_id_index"),
    ]

    operations = [
        migrations.RunPython(forward, migrations.RunPython.noop),
    ]
