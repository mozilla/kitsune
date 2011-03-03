CREATE TABLE `postcrash_signature` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `signature` varchar(255) NOT NULL UNIQUE,
    `document_id` integer NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci
;
ALTER TABLE `postcrash_signature` ADD CONSTRAINT `document_id_refs_id_4d433fd5` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`);
CREATE INDEX `postcrash_signature_f4226d13` ON `postcrash_signature` (`document_id`);
