-- Announcement model
CREATE TABLE `announcements_announcement` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `created` datetime NOT NULL,
    `creator_id` integer NOT NULL,
    `show_after` datetime NOT NULL,
    `show_until` datetime,
    `content` longtext NOT NULL,
    `group_id` integer
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `announcements_announcement` ADD CONSTRAINT `creator_id_refs_id_1b56d8` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `announcements_announcement` ADD CONSTRAINT `group_id_refs_id_685bd3c7` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);
CREATE INDEX `announcements_announcement_f97a5119` ON `announcements_announcement` (`creator_id`);
CREATE INDEX `announcements_announcement_3c9f0fe7` ON `announcements_announcement` (`show_after`);
CREATE INDEX `announcements_announcement_d63a60f1` ON `announcements_announcement` (`show_until`);
CREATE INDEX `announcements_announcement_bda51c3c` ON `announcements_announcement` (`group_id`);

-- Auth permissions
INSERT INTO django_content_type (`name`, `app_label`, `model`) VALUES
    ('announcement', 'announcements', 'announcement');

SET @ct = LAST_INSERT_ID();

INSERT INTO auth_permission (`name`, `content_type_id`, `codename`) VALUES
    ('Can add announcement', @ct, 'add_announcement'),
    ('Can change announcement', @ct, 'change_announcement'),
    ('Can delete announcement', @ct, 'delete_announcement');
