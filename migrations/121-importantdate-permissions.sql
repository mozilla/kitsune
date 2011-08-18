INSERT IGNORE INTO django_content_type (`name`, `app_label`, `model`) VALUES
    ('important date', 'wiki', 'importantdate');

SET @ct = (SELECT id FROM django_content_type WHERE model='importantdate');

INSERT INTO auth_permission (`name`, `content_type_id`, `codename`) VALUES
    ('Can add important dates', @ct, 'add_importantdate'),
    ('Can change important dates', @ct, 'change_importantdate'),
    ('Can delete important dates', @ct, 'delete_importantdate');
