from django.db import migrations


def create_community_team(apps, schema_editor):
    """Create the Community Team group with a GroupProfile."""
    from django.template.defaultfilters import slugify
    
    Group = apps.get_model('auth', 'Group')
    GroupProfile = apps.get_model('groups', 'GroupProfile')
    
    group, created = Group.objects.get_or_create(name="Community Team")
    
    if not GroupProfile.objects.filter(group=group).exists():
        GroupProfile.objects.create(
            group=group,
            slug=slugify(group.name),
            information="The Community Team helps welcome and support new contributors to Mozilla Support.",
            information_html="The Community Team helps welcome and support new contributors to Mozilla Support."
        )


def reverse_create_community_team(apps, schema_editor):
    """Remove the Community Team group and profile."""
    Group = apps.get_model('auth', 'Group')
    GroupProfile = apps.get_model('groups', 'GroupProfile')
    
    try:
        group = Group.objects.get(name="Community Team")
        GroupProfile.objects.filter(group=group).delete()
        group.delete()
    except Group.DoesNotExist:
        pass


class Migration(migrations.Migration):

    dependencies = [
        ('groups', '0004_add_staff_content_team_profile'),
    ]

    operations = [
        migrations.RunPython(
            create_community_team,
            reverse_create_community_team,
        ),
    ]