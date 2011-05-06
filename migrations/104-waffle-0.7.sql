-- Upgrade to Waffle 0.7.2

ALTER TABLE `waffle_flag` ADD COLUMN `note` LONGTEXT NOT NULL;
ALTER TABLE `waffle_sample` ADD COLUMN `note` LONGTEXT NOT NULL;
ALTER TABLE `waffle_switch` ADD COLUMN `note` LONGTEXT NOT NULL;
