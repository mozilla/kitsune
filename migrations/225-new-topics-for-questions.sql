CREATE TABLE `questions_question_new_topics` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `question_id` integer NOT NULL,
    `topic_id` integer NOT NULL,
    UNIQUE (`question_id`, `topic_id`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

ALTER TABLE `questions_question_new_topics` ADD CONSTRAINT `topic_id_refs_id_59a87030` FOREIGN KEY (`topic_id`) REFERENCES `products_topic` (`id`);
