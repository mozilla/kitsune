CREATE TABLE `activity_activity` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `creator_id` integer,
    `created` datetime NOT NULL,
    `title` varchar(120) NOT NULL,
    `content` varchar(400) NOT NULL,
    `url` varchar(200),
    `content_type_id` integer,
    `object_id` integer UNSIGNED
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

ALTER TABLE `activity_activity` ADD CONSTRAINT `user_id_refs_id_a9d97970` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `activity_activity` ADD CONSTRAINT `creator_id_refs_id_a9d97970` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `activity_activity` ADD CONSTRAINT `content_type_id_refs_id_4349db6c` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);
CREATE INDEX `activity_activity_e569965d` ON `activity_activity` (`user_id`);
CREATE INDEX `activity_activity_f97a5119` ON `activity_activity` (`creator_id`);
CREATE INDEX `activity_activity_3216ff68` ON `activity_activity` (`created`);
CREATE INDEX `activity_activity_e4470c6e` ON `activity_activity` (`content_type_id`);
