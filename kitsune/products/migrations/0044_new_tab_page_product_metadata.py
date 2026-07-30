from django.db import migrations

DESCRIPTION_ADDITIONS = {
    "Firefox": (
        "Opening a new tab, a new window, or the browser itself shows the New Tab page, also"
        " known as Firefox Home or the start page. It can display a web search box, Shortcuts"
        " to frequently visited sites, recommended stories, many kinds of widgets (weather,"
        " clock, timer, crossword, etc.), and a wallpaper, and each of these sections can be"
        " shown or hidden from the settings button on the page itself."
    ),
    "Firefox for Android": (
        "Opening a new tab or the app itself shows the homepage, also known as Firefox Home."
        " It can display a search box, Shortcuts to frequently visited sites, recently saved"
        ' bookmarks, recently visited pages, a "Jump back in" section for resuming recent'
        " browsing, recommended stories, and a wallpaper, and each of these sections can be"
        " shown or hidden from the app's settings."
    ),
    "Firefox for iOS": (
        "Opening a new tab or the app itself shows the homepage, also known as Firefox Home."
        " It can display a search box, Shortcuts to frequently visited sites, recently saved"
        ' bookmarks, a "Jump back in" section for resuming recent browsing, recommended'
        " stories, and a wallpaper, and each of these sections can be shown or hidden from the"
        " app's settings."
    ),
}

ALREADY_COVERED_MARKERS = ("new tab", "firefox home")


def add_new_tab_page_metadata(apps, schema_editor):
    """
    Extend the product descriptions used by the LLM classifiers to cover the New Tab page.

    Appends rather than replaces, because these descriptions are editable in the admin and
    may have diverged from the text seeded by earlier migrations.
    """
    Product = apps.get_model("products", "Product")

    for title, addition in DESCRIPTION_ADDITIONS.items():
        try:
            product = Product.objects.get(title=title, is_archived=False)
        except Product.DoesNotExist:
            print(f"""Skipped product "{title}" because it does not exist.""")
            continue
        except Product.MultipleObjectsReturned:
            print(f"""Skipped product "{title}" because it has multiple objects.""")
            continue

        metadata = product.metadata if isinstance(product.metadata, dict) else {}
        description = metadata.get("description")

        if not isinstance(description, str) or not description.strip():
            print(f"""Skipped product "{title}" because it has no description to extend.""")
            continue

        description = description.strip()

        if any(marker in description.lower() for marker in ALREADY_COVERED_MARKERS):
            print(
                f"""Skipped product "{title}" because its description already covers"""
                " the New Tab page."
            )
            continue

        product.metadata = metadata | {"description": f"{description} {addition}"}
        product.save()


class Migration(migrations.Migration):
    dependencies = [
        ("products", "0043_topic_article_ordering"),
    ]

    operations = [
        migrations.RunPython(add_new_tab_page_metadata, migrations.RunPython.noop),
    ]
