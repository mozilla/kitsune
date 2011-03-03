INSERT INTO django_content_type (`name`, `app_label`, `model`) VALUES
    ('image attachment', 'upload', 'imageattachment');

SET @ct = LAST_INSERT_ID();

INSERT INTO auth_permission (`name`, `content_type_id`, `codename`) VALUES
    ('Can add image attachments', @ct, 'add_imageattachment'),
    ('Can change image attachments', @ct, 'change_imageattachment'),
    ('Can delete image attachments', @ct, 'delete_imageattachment');
