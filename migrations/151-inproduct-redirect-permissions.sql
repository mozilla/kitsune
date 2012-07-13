SELECT (@id:=`id`) FROM `django_content_type` WHERE `name` = 'redirect';

INSERT INTO auth_permission (`name`, `content_type_id`, `codename`) VALUES
    ('Can add inproduct redirects', @id, 'add_redirect'),
    ('Can change inproduct redirects', @id, 'change_redirect'),
    ('Can delete inproduct redirects', @id, 'delete_redirect');
