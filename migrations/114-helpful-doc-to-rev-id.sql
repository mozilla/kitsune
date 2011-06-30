RENAME TABLE `wiki_helpfulvote` TO `wiki_helpfulvoteold`;

CREATE TABLE `wiki_helpfulvote` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `revision_id` integer NOT NULL,
    `helpful` bool NOT NULL,
    `created` datetime NOT NULL,
    `creator_id` integer,
    `anonymous_id` varchar(40) NOT NULL,
    `user_agent` varchar(1000) NOT NULL
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

ALTER TABLE `wiki_helpfulvote` ADD CONSTRAINT `creator_id_refs_id_4ec8a21b` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `wiki_helpfulvote` ADD CONSTRAINT `revision_id_refs_id_a55647b` FOREIGN KEY (`revision_id`) REFERENCES `wiki_revision` (`id`);

CREATE INDEX `wiki_helpfulvote_202bdc7f` ON `wiki_helpfulvote` (`revision_id`);
CREATE INDEX `wiki_helpfulvote_3216ff68` ON `wiki_helpfulvote` (`created`);
CREATE INDEX `wiki_helpfulvote_685aee7` ON `wiki_helpfulvote` (`creator_id`);
CREATE INDEX `wiki_helpfulvote_2291b592` ON `wiki_helpfulvote` (`anonymous_id`);
