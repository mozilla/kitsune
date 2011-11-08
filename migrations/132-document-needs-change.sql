-- Add needs_change flag and comment to wiki documents:
ALTER TABLE `wiki_document` ADD `needs_change` bool NOT NULL;
ALTER TABLE `wiki_document` ADD `needs_change_comment` varchar(500) NOT NULL;

CREATE INDEX `wiki_document_c764d599` ON `wiki_document` (`needs_change`);
