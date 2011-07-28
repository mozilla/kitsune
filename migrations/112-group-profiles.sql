CREATE TABLE `groups_groupprofile_leaders` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `groupprofile_id` integer NOT NULL,
    `user_id` integer NOT NULL,
    UNIQUE (`groupprofile_id`, `user_id`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci
;
ALTER TABLE `groups_groupprofile_leaders` ADD CONSTRAINT `user_id_refs_id_82107ee1` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `groups_groupprofile` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `slug` varchar(80) NOT NULL UNIQUE,
    `group_id` integer NOT NULL,
    `information` longtext NOT NULL,
    `information_html` longtext NOT NULL,
    `avatar` varchar(250)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci
;
ALTER TABLE `groups_groupprofile` ADD CONSTRAINT `group_id_refs_id_acfd2c6f` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);
ALTER TABLE `groups_groupprofile_leaders` ADD CONSTRAINT `groupprofile_id_refs_id_607797bc` FOREIGN KEY (`groupprofile_id`) REFERENCES `groups_groupprofile` (`id`);
CREATE INDEX `groups_groupprofile_bda51c3c` ON `groups_groupprofile` (`group_id`);

INSERT INTO django_content_type (`name`, `app_label`, `model`) VALUES
    ('group profile', 'groups', 'groupprofile');
SET @ct = LAST_INSERT_ID();
INSERT INTO auth_permission (`name`, `content_type_id`, `codename`) VALUES
    ('Can add group profile', @ct, 'add_groupprofile'),
    ('Can change group profile', @ct, 'change_groupprofile'),
    ('Can delete group profile', @ct, 'delete_groupprofile');
