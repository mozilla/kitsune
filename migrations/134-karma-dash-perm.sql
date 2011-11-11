SET @ct = (SELECT id from django_content_type WHERE name='title' AND app_label='karma');

INSERT INTO auth_permission (`name`, `content_type_id`, `codename`) VALUES
    ('Can access karma dashboard', @ct, 'view_dashboard');
