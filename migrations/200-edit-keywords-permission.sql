SET @ct = (SELECT id from django_content_type WHERE name='revision' AND app_label='wiki');

INSERT INTO auth_permission (`name`, `content_type_id`, `codename`) VALUES
    ('Can edit keywords', @ct, 'edit_keywords');