/* Allow NULL because the only sane default I can think of (en-US)
 * may not exist. */
ALTER TABLE `questions_question` ADD COLUMN `locale_id` integer NULL;
ALTER TABLE `questions_question` ADD CONSTRAINT `locale_id_refs_id_643d2ff3` FOREIGN KEY (`locale_id`) REFERENCES `wiki_locale` (`id`);

