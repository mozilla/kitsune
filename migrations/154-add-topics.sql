CREATE TABLE `topics_topic` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `title` varchar(255) NOT NULL,
    `slug` varchar(50) NOT NULL,
    `description` longtext NOT NULL,
    `image` varchar(250),
    `parent_id` integer,
    `display_order` integer NOT NULL,
    `visible` bool NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

ALTER TABLE `topics_topic` ADD CONSTRAINT `parent_id_refs_id_39bb1195` FOREIGN KEY (`parent_id`) REFERENCES `topics_topic` (`id`);
CREATE INDEX `topics_topic_841a7e28` ON `topics_topic` (`title`);
CREATE INDEX `topics_topic_a951d5d6` ON `topics_topic` (`slug`);
CREATE INDEX `topics_topic_63f17a16` ON `topics_topic` (`parent_id`);

INSERT INTO `django_content_type` (`name`, `app_label`, `model`) VALUES ('topic','topics','topic');

SELECT (@id:=`id`) FROM `django_content_type` WHERE `name` = 'topic';

INSERT INTO `auth_permission` (`name`, `content_type_id`, `codename`) VALUES ('Can add topic',@id,'add_topic'),('Can change topic',@id,'change_topic'),('Can delete topic',@id,'delete_topic');
