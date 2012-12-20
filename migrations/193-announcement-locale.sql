ALTER TABLE `announcements_announcement` ADD `locale_id` integer;
ALTER TABLE `announcements_announcement` ADD CONSTRAINT `locale_id_refs_id_ac0886f3` FOREIGN KEY (`locale_id`) REFERENCES `wiki_locale` (`id`);
