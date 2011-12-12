-- Add new waffle_* columns.
ALTER TABLE `waffle_flag` ADD `testing` bool NOT NULL;
ALTER TABLE `waffle_flag` ADD `created` datetime NOT NULL;
ALTER TABLE `waffle_flag` ADD `modified` datetime NOT NULL;

ALTER TABLE `waffle_switch` ADD `created` datetime NOT NULL;
ALTER TABLE `waffle_switch` ADD `modified` datetime NOT NULL;

ALTER TABLE `waffle_sample` ADD `created` datetime NOT NULL;
ALTER TABLE `waffle_sample` ADD `modified` datetime NOT NULL;

CREATE INDEX `waffle_flag_3216ff68` ON `waffle_flag` (`created`);
CREATE INDEX `waffle_switch_3216ff68` ON `waffle_switch` (`created`);
CREATE INDEX `waffle_sample_3216ff68` ON `waffle_sample` (`created`);
