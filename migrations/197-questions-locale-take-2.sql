ALTER TABLE `questions_question`
    DROP FOREIGN KEY `locale_id_refs_id_643d2ff3`,
    DROP COLUMN `locale_id`,
    ADD COLUMN `locale` varchar(7) NOT NULL DEFAULT 'en-US';

