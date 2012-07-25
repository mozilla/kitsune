CREATE TABLE `wiki_document_topics` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `document_id` integer NOT NULL,
    `topic_id` integer NOT NULL,
    UNIQUE (`document_id`, `topic_id`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

ALTER TABLE `wiki_document_topics` ADD CONSTRAINT `topic_id_refs_id_f0454a8c` FOREIGN KEY (`topic_id`) REFERENCES `topics_topic` (`id`);

ALTER TABLE `wiki_document_topics` ADD CONSTRAINT `document_id_refs_id_1d391341` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`);
