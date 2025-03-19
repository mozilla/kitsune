from django.db import migrations, transaction
from django.db.models import Q


def delete_non_migrated_users(apps, schema_editor):
    """
    Delete users in batches where is_fxa_migrated is False or null
    """
    User = apps.get_model('auth', 'User')
    Profile = apps.get_model('users', 'Profile')
    db_alias = schema_editor.connection.alias
    
    BATCH_SIZE = 1000
    
    def process_batch():
        # Use select_related to get user data in the same query
        # This avoids the separate query for User objects
        profiles = Profile.objects.using(db_alias).select_related('user').filter(
            Q(is_fxa_migrated__isnull=True) | Q(is_fxa_migrated=False)
        )[:BATCH_SIZE]
        
        # Evaluate query and check if we have results
        if not profiles.exists():
            return False
            
        # Process deletions in a transaction to ensure consistency
        with transaction.atomic(using=db_alias):
            # Get all users in one go with their related profiles
            users = User.objects.using(db_alias).filter(
                id__in=profiles.values_list('user_id', flat=True)
            ).select_related('profile')
            
            # Delete users in chunks to balance between bulk operations and signal handling
            chunk_size = 100  # Smaller chunks for signal handling but still efficient
            users_list = list(users)  # Already fetched, so no extra query
            
            for i in range(0, len(users_list), chunk_size):
                chunk = users_list[i:i + chunk_size]
                # Delete users in the chunk
                for user in chunk:
                    user.delete()  # Will trigger signals
                
        return True

    # Process batches until no more users are found
    while process_batch():
        pass


def reverse_migration(apps, schema_editor):
    """
    No reverse migration possible since deletion cannot be undone
    """
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0032_profile_account_type_alter_profile_user'),
    ]

    operations = [
        migrations.RunPython(
            delete_non_migrated_users,
            reverse_migration,
        ),
    ] 