from django.db import migrations
from django.db.models import Exists, OuterRef
from django.utils.text import slugify

from kitsune.wiki.config import REDIRECT_HTML


def make_unique(value, taken, max_length, separator):
    unique = value[:max_length]
    suffix = 2
    while unique in taken:
        tail = f"{separator}{suffix}"
        unique = value[: max_length - len(tail)] + tail
        suffix += 1
    taken.add(unique)
    return unique


def forward(apps, schema_editor):
    Audience = apps.get_model("wiki", "Audience")
    Document = apps.get_model("wiki", "Document")
    DocumentAudience = apps.get_model("wiki", "DocumentAudience")
    DocumentLink = apps.get_model("wiki", "DocumentLink")
    Group = apps.get_model("auth", "Group")

    public, _created = Audience.objects.get_or_create(slug="public", defaults={"name": "Public"})

    restrictions = {}
    for document_id, group_id in Document.restrict_to_groups.through.objects.filter(
        document__parent__isnull=True
    ).values_list("document_id", "group_id"):
        restrictions.setdefault(document_id, set()).add(group_id)

    taken_names = set(Audience.objects.values_list("name", flat=True))
    taken_slugs = set(Audience.objects.values_list("slug", flat=True))
    name_length = Audience._meta.get_field("name").max_length
    slug_length = Audience._meta.get_field("slug").max_length
    audience_by_group = {}
    for group in Group.objects.filter(id__in=set().union(*restrictions.values())).order_by("id"):
        # The Public audience holds "Public", and "Public 2" would read as public too.
        name = f"{group.name} (restricted)" if group.name == "Public" else group.name
        audience_by_group[group.id] = Audience(
            name=make_unique(name, taken_names, name_length, " "),
            slug=make_unique(slugify(name) or "audience", taken_slugs, slug_length, "-"),
        )
    Audience.objects.bulk_create(audience_by_group.values())
    Audience.groups.through.objects.bulk_create(
        Audience.groups.through(audience_id=audience.id, group_id=group_id)
        for group_id, audience in audience_by_group.items()
    )

    stub_ids = set(
        Document.objects.filter(html__startswith=REDIRECT_HTML).values_list("id", flat=True)
    )
    links = {}
    parent_of = {}
    for stub_id, target_id, target_parent_id in (
        DocumentLink.objects.filter(kind="link", linked_from__html__startswith=REDIRECT_HTML)
        .order_by("id")
        .values_list("linked_from_id", "linked_to_id", "linked_to__parent_id")
    ):
        # A stub with several links follows its lowest-id link, so the mapping is deterministic.
        links.setdefault(stub_id, target_id)
        parent_of[target_id] = target_parent_id

    unassigned = (
        Document.objects.filter(
            ~Exists(DocumentAudience.objects.filter(document=OuterRef("pk"))), parent__isnull=True
        )
        .order_by("id")
        .values_list("id", flat=True)
    )
    document_audiences = []
    for document_id in unassigned:
        source_id = document_id
        if document_id in stub_ids:
            visited = {document_id}
            target_id = links.get(document_id)
            while target_id in stub_ids and target_id not in visited:
                visited.add(target_id)
                target_id = links.get(target_id)
            if target_id is not None and target_id not in stub_ids:
                source_id = parent_of[target_id] or target_id

        group_ids = restrictions.get(source_id)
        audience_ids = (
            [audience_by_group[group_id].id for group_id in sorted(group_ids)]
            if group_ids
            else [public.id]
        )
        document_audiences.extend(
            DocumentAudience(document_id=document_id, audience_id=audience_id)
            for audience_id in audience_ids
        )
    DocumentAudience.objects.bulk_create(document_audiences, batch_size=1000)


def backward(apps, schema_editor):
    apps.get_model("wiki", "DocumentAudience").objects.all().delete()
    apps.get_model("wiki", "Audience").objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("wiki", "0026_audience_documentaudience_document_audiences_and_more"),
    ]

    operations = [
        migrations.RunPython(forward, backward),
    ]
