CREATE TABLE `dashboards_groupdashboard` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `group_id` integer NOT NULL,
    `dashboard` varchar(200) NOT NULL,
    `parameters` varchar(255) NOT NULL
);
ALTER TABLE `dashboards_groupdashboard` ADD CONSTRAINT `group_id_refs_id_142d6845` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);
CREATE INDEX `dashboards_groupdashboard_bda51c3c` ON `dashboards_groupdashboard` (`group_id`);

INSERT INTO django_content_type (`name`, `app_label`, `model`) VALUES
    ('group dashboard', 'dashboards', 'groupdashboard');
SET @ct = LAST_INSERT_ID();
INSERT INTO auth_permission (`name`, `content_type_id`, `codename`) VALUES
    ('Can add group dashboard', @ct, 'add_groupdashboard'),
    ('Can change group dashboard', @ct, 'change_groupdashboard'),
    ('Can delete group dashboard', @ct, 'delete_groupdashboard');
