SET @ct = (SELECT id from django_content_type WHERE name='profile' AND app_label='users');

INSERT INTO auth_permission (`name`, `content_type_id`, `codename`) VALUES
    ('Can deactivate users', @ct, 'deactivate_users');