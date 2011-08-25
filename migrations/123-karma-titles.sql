CREATE TABLE `karma_title_users` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `title_id` integer NOT NULL,
    `user_id` integer NOT NULL,
    UNIQUE (`title_id`, `user_id`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci
;
ALTER TABLE `karma_title_users` ADD CONSTRAINT `user_id_refs_id_83fda647` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `karma_title_groups` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `title_id` integer NOT NULL,
    `group_id` integer NOT NULL,
    UNIQUE (`title_id`, `group_id`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci
;
ALTER TABLE `karma_title_groups` ADD CONSTRAINT `group_id_refs_id_b8eda48d` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);
CREATE TABLE `karma_title` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `name` varchar(100) NOT NULL UNIQUE
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci
;
ALTER TABLE `karma_title_users` ADD CONSTRAINT `title_id_refs_id_898b376c` FOREIGN KEY (`title_id`) REFERENCES `karma_title` (`id`);
ALTER TABLE `karma_title_groups` ADD CONSTRAINT `title_id_refs_id_2468f187` FOREIGN KEY (`title_id`) REFERENCES `karma_title` (`id`);

INSERT INTO django_content_type (`name`, `app_label`, `model`) VALUES
    ('title', 'karma', 'title');
SET @ct = LAST_INSERT_ID();
INSERT INTO auth_permission (`name`, `content_type_id`, `codename`) VALUES
    ('Can add title', @ct, 'add_title'),
    ('Can change title', @ct, 'change_title'),
    ('Can delete title', @ct, 'delete_title');
