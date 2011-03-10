DROP TABLE `activity_activity`;

CREATE TABLE `activity_action_users` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `action_id` integer NOT NULL,
    `user_id` integer NOT NULL,
    UNIQUE (`action_id`, `user_id`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

ALTER TABLE `activity_action_users` ADD CONSTRAINT `user_id_refs_id_514426b8` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

CREATE TABLE `activity_action` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `creator_id` integer,
    `created` datetime NOT NULL,
    `data` varchar(400) NOT NULL,
    `url` varchar(200),
    `content_type_id` integer,
    `object_id` integer UNSIGNED,
    `formatter_cls` varchar(200) NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

ALTER TABLE `activity_action` ADD CONSTRAINT `creator_id_refs_id_4475b305` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `activity_action` ADD CONSTRAINT `content_type_id_refs_id_95f5c947` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
ALTER TABLE `activity_action_users` ADD CONSTRAINT `action_id_refs_id_52ad1f42` FOREIGN KEY (`action_id`) REFERENCES `activity_action` (`id`);
CREATE INDEX `activity_action_f97a5119` ON `activity_action` (`creator_id`);
CREATE INDEX `activity_action_3216ff68` ON `activity_action` (`created`);
CREATE INDEX `activity_action_e4470c6e` ON `activity_action` (`content_type_id`);

