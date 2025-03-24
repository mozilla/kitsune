from django.db import migrations


def create_staff_content_team_profile(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    GroupProfile = apps.get_model('groups', 'GroupProfile')

    try:
        group = Group.objects.get(name='Staff Content Team')
        # Create the group profile if it doesn't exist
        if not GroupProfile.objects.filter(group=group).exists():
            GroupProfile.objects.create(
                group=group,
                information='Staff Content Team group for content management.',
                information_html='Staff Content Team group for content management.'
            )
    except Group.DoesNotExist:
        raise Exception("Staff Content Team group must exist before running this migration")


def remove_staff_content_team_profile(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    GroupProfile = apps.get_model('groups', 'GroupProfile')

    try:
        group = Group.objects.get(name='Staff Content Team')
        GroupProfile.objects.filter(group=group).delete()
    except Group.DoesNotExist:
        pass


class Migration(migrations.Migration):
    dependencies = [
        ('groups', '0003_auto_20250218_1157'),
    ]

    operations = [
        migrations.RunPython(
            create_staff_content_team_profile,
            remove_staff_content_team_profile
        ),
    ] 
