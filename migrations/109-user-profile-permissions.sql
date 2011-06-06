SET @ct = (SELECT id from django_content_type WHERE name='profile' AND app_label='users');

INSERT INTO auth_permission (`name`, `content_type_id`, `codename`) VALUES
    ('Can add user profiles', @ct, 'add_profile'),
    ('Can change user profiles', @ct, 'change_profile'),
    ('Can delete user profiles', @ct, 'delete_profile');
