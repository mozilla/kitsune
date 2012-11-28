CREATE TABLE `questions_question_topics` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `question_id` integer NOT NULL,
    `topic_id` integer NOT NULL,
    UNIQUE (`question_id`, `topic_id`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `questions_question_topics` ADD CONSTRAINT `topic_id_refs_id_cd2cd363` FOREIGN KEY (`topic_id`) REFERENCES `topics_topic` (`id`);
ALTER TABLE `questions_question_topics` ADD CONSTRAINT `question_id_refs_id_209b8179` FOREIGN KEY (`question_id`) REFERENCES `questions_question` (`id`);

CREATE TABLE `questions_question_products` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `question_id` integer NOT NULL,
    `product_id` integer NOT NULL,
    UNIQUE (`question_id`, `product_id`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `questions_question_products` ADD CONSTRAINT `product_id_refs_id_d86bc827` FOREIGN KEY (`product_id`) REFERENCES `products_product` (`id`);
ALTER TABLE `questions_question_products` ADD CONSTRAINT `question_id_refs_id_4ad2f9d9` FOREIGN KEY (`question_id`) REFERENCES `questions_question` (`id`);
