CREATE TABLE `wiki_documentlink` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `linked_from_id` integer NOT NULL,
    `linked_to_id` integer NOT NULL,
    `kind` varchar(16) NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

ALTER TABLE `wiki_documentlink`
    ADD CONSTRAINT `linked_from_id_refs_id_8da923a9`
    FOREIGN KEY (`linked_from_id`)
    REFERENCES `wiki_document` (`id`);

ALTER TABLE `wiki_documentlink`
    ADD CONSTRAINT `linked_to_id_refs_id_8da923a9`
    FOREIGN KEY (`linked_to_id`)
    REFERENCES `wiki_document` (`id`);
