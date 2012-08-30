ALTER TABLE `forums_forum` ADD `display_order` integer NOT NULL DEFAULT 1;
ALTER TABLE `forums_forum` ADD `is_listed` bool NOT NULL DEFAULT 1;

CREATE INDEX `forums_forum_17fce74f` ON `forums_forum` (`display_order`);
CREATE INDEX `forums_forum_18046f5a` ON `forums_forum` (`is_listed`);
