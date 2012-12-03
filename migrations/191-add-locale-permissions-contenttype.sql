INSERT IGNORE INTO `django_content_type` (`name`, `app_label`, `model`) VALUES ('locale','wiki','locale') ON DUPLICATE KEY UPDATE `name`='locale';

SELECT (@id:=`id`) FROM `django_content_type` WHERE `name` = 'locale';

INSERT INTO auth_permission (`name`, `content_type_id`, `codename`) VALUES
    ('Can add wiki locales', @id, 'add_locale'),
    ('Can change wiki locales', @id, 'change_locale'),
    ('Can delete wiki locales', @id, 'delete_locale');
