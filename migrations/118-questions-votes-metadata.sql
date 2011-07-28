CREATE TABLE `questions_votemetadata` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `content_type_id` integer,
    `object_id` integer UNSIGNED,
    `key` varchar(40) NOT NULL,
    `value` varchar(1000) NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci
;
ALTER TABLE `questions_votemetadata` ADD CONSTRAINT `content_type_id_refs_id_f18225bf` FOREIGN KEY (`content_type_id`) REFERENCES `django_content_type` (`id`);

CREATE INDEX `questions_votemetadata_e4470c6e` ON `questions_votemetadata` (`content_type_id`);
CREATE INDEX `questions_votemetadata_45544485` ON `questions_votemetadata` (`key`);
