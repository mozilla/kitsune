from django.core.management.base import BaseCommand
from fuzzywuzzy import fuzz

from kitsune.tags.models import SumoTag, SumoTaggedItem

SIMILARITY_THRESHOLD = 75


class Command(BaseCommand):
    help = "Merge similar tags"

    def handle(self, *args, **kwargs):
        def recursively_merge_tags(tag_ids):
            merged_any = False
            deleted_tags = set()

            for i, primary_tag_id in enumerate(tag_ids):
                if primary_tag_id in deleted_tags:
                    continue

                primary_tag = SumoTag.objects.get(id=primary_tag_id)
                if primary_tag.slug.startswith("seg-"):
                    continue

                for secondary_tag_id in tag_ids[i + 1 :]:
                    if secondary_tag_id in deleted_tags:
                        continue

                    secondary_tag = SumoTag.objects.get(id=secondary_tag_id)
                    similarity = fuzz.ratio(primary_tag.name, secondary_tag.name)
                    if similarity >= SIMILARITY_THRESHOLD:
                        duplicate_conflicts = SumoTaggedItem.objects.filter(
                            tag=secondary_tag,
                            object_id__in=SumoTaggedItem.objects.filter(
                                tag=primary_tag
                            ).values_list("object_id", flat=True),
                        )
                        duplicate_conflicts.delete()

                        SumoTaggedItem.objects.filter(tag=secondary_tag).update(tag=primary_tag)

                        secondary_tag.delete()
                        deleted_tags.add(secondary_tag_id)

                        print(f"Merged '{secondary_tag.name}' into '{primary_tag.name}'")
                        merged_any = True
                        break  # start over

            if merged_any:
                remaining_tag_ids = (
                    SumoTag.objects.exclude(id__in=deleted_tags)
                    .order_by("-id")
                    .values_list("id", flat=True)
                )
                return recursively_merge_tags(list(remaining_tag_ids))

        tag_ids = SumoTag.objects.all().order_by("-id").values_list("id", flat=True)
        recursively_merge_tags(list(tag_ids))
