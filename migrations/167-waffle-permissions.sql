INSERT IGNORE INTO `django_content_type` (`name`, `app_label`, `model`) VALUES
	('flag','waffle','flag'),
	('sample','waffle','sample'),
	('switch','waffle','switch');

SELECT (@flagid:=`id`) FROM `django_content_type` WHERE `name` = 'flag';
SELECT (@sampleid:=`id`) FROM `django_content_type` WHERE `name` = 'sample';
SELECT (@switchid:=`id`) FROM `django_content_type` WHERE `name` = 'switch';

INSERT INTO auth_permission (`name`, `content_type_id`, `codename`) VALUES
    ('Can add waffle flags', @flagid, 'add_flag'),
    ('Can change waffle flags', @flagid, 'change_flag'),
    ('Can delete waffle flags', @flagid, 'delete_flag'),
    ('Can add waffle samples', @sampleid, 'add_sample'),
    ('Can change waffle samples', @sampleid, 'change_sample'),
    ('Can delete waffle samples', @sampleid, 'delete_sample'),
    ('Can add waffle switches', @switchid, 'add_switch'),
    ('Can change waffle switches', @switchid, 'change_switch'),
    ('Can delete waffle switches', @switchid, 'delete_switch');
