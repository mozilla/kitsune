/* Allow NULL because the only sane default I can think of (en-US)
 * may not exist. */
ALTER TABLE `questions_question` ADD COLUMN `locale_id` integer NULL;
ALTER TABLE `questions_question` ADD CONSTRAINT `locale_id_refs_id_643d2ff3` FOREIGN KEY (`locale_id`) REFERENCES `wiki_locale` (`id`);

ALTER TABLE `questions_question` ADD COLUMN `product_id` integer NULL;
ALTER TABLE `questions_question` ADD CONSTRAINT `product_id_refs_id_9659be74` FOREIGN KEY (`locale_id`) REFERENCES `products_product` (`id`);

ALTER TABLE `questions_question` ADD COLUMN `topic_id` integer NULL;
ALTER TABLE `questions_question` ADD CONSTRAINT `topic_id_refs_id_b4f2f293` FOREIGN KEY (`locale_id`) REFERENCES `topics_topic` (`id`);

