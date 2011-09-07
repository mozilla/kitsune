CREATE TABLE `wiki_helpfulvotemetadata` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `vote_id` integer NOT NULL,
    `key` varchar(40) NOT NULL,
    `value` varchar(1000) NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci
;
ALTER TABLE `wiki_helpfulvotemetadata` ADD CONSTRAINT `vote_id_refs_id_3a2685f2` FOREIGN KEY (`vote_id`) REFERENCES `wiki_helpfulvote` (`id`);
CREATE INDEX `wiki_helpfulvotemetadata_f65ecc44` ON `wiki_helpfulvotemetadata` (`vote_id`);
CREATE INDEX `wiki_helpfulvotemetadata_45544485` ON `wiki_helpfulvotemetadata` (`key`);
