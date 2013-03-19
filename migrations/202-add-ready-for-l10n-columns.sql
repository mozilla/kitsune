ALTER TABLE `wiki_revision`
    ADD COLUMN `readied_for_localization` datetime,

    ADD COLUMN `readied_for_localization_by_id` integer,
    ADD CONSTRAINT `readied_for_localization_by_id_refs_id_4298f2ad` FOREIGN KEY (`readied_for_localization_by_id`) REFERENCES `auth_user` (`id`);

CREATE INDEX `wiki_revision_e4f0dcb5` ON `wiki_revision` (`readied_for_localization_by_id`);

UPDATE `wiki_revision`
    SET `readied_for_localization` = `reviewed`,
        `readied_for_localization_by_id` = `reviewer_id`
    WHERE `is_ready_for_localization` = 1;
