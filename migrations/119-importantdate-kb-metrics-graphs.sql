CREATE TABLE `wiki_importantdate` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `text` varchar(100) NOT NULL,
    `date` datetime NOT NULL
) ENGINE=InnoDB  DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;

CREATE INDEX `wiki_importantdate_679343db` ON `wiki_importantdate` (`date`);
