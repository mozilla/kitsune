/* Allow NULL because the only sane default I can think of (en-US)
 * may not exist. */
ALTER TABLE `questions_question`
    ADD COLUMN `locale_id` integer NULL,
    ADD CONSTRAINT `locale_id_refs_id_643d2ff3` FOREIGN KEY (`locale_id`) REFERENCES `wiki_locale` (`id`),

    ADD COLUMN `product_id` integer NULL,
    ADD CONSTRAINT `product_id_refs_id_9659be74` FOREIGN KEY (`product_id`) REFERENCES `products_product` (`id`),

    ADD COLUMN `topic_id` integer NULL,
    ADD CONSTRAINT `topic_id_refs_id_b4f2f293` FOREIGN KEY (`topic_id`) REFERENCES `topics_topic` (`id`);

