SET @ct = (SELECT id from django_content_type WHERE name='document' AND app_label='wiki');

INSERT INTO auth_permission (`name`, `content_type_id`, `codename`) VALUES
    ('Can edit needs_change', @ct, 'edit_needs_change');
