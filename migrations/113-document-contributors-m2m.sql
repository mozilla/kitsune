CREATE TABLE `wiki_document_contributors` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `document_id` integer NOT NULL,
    `user_id` integer NOT NULL,
    UNIQUE (`document_id`, `user_id`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci
;
ALTER TABLE `wiki_document_contributors` ADD CONSTRAINT `user_id_refs_id_12d875b` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `wiki_document_contributors` ADD CONSTRAINT `document_id_refs_id_a223b3cf` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`);
