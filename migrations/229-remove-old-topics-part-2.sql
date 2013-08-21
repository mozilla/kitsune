DROP TABLE `questions_question_topics`;

ALTER TABLE `questions_question` DROP FOREIGN KEY `topic_id_refs_id_b4f2f2931`;

ALTER TABLE `questions_question` DROP `topic_id`;

ALTER TABLE `topics_topic` DROP FOREIGN KEY `parent_id_refs_id_39bb1195`;

DROP TABLE `topics_topic`;

-- Duplicate `questions_question_new_topics`

CREATE TABLE `questions_question_topics` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `question_id` integer NOT NULL,
    `topic_id` integer NOT NULL,
    UNIQUE (`question_id`, `topic_id`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

ALTER TABLE `questions_question_topics` ADD CONSTRAINT `topic_id_refs_id_59a87031` FOREIGN KEY (`topic_id`) REFERENCES `products_topic` (`id`);

INSERT `questions_question_topics` SELECT * FROM `questions_question_new_topics`;

-- Duplicate `wiki_document_new_topics`

CREATE TABLE `wiki_document_topics` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `document_id` integer NOT NULL,
    `topic_id` integer NOT NULL,
    UNIQUE (`document_id`, `topic_id`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

ALTER TABLE `wiki_document_topics` ADD CONSTRAINT `document_id_refs_id_e73cc77f` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`);
ALTER TABLE `wiki_document_topics` ADD CONSTRAINT `topic_id_refs_id_39036d42` FOREIGN KEY (`topic_id`) REFERENCES `products_topic` (`id`);

INSERT `wiki_document_topics` SELECT * FROM `wiki_document_new_topics`;
