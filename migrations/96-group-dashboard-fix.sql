-- Largely supersede migration 95.
-- Fix `dashboard` column width, engine, and charset.

DROP TABLE dashboards_groupdashboard;

CREATE TABLE `dashboards_groupdashboard` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `group_id` integer NOT NULL,
    `dashboard` varchar(10) NOT NULL,
    `parameters` varchar(255) NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `dashboards_groupdashboard` ADD CONSTRAINT `group_id_refs_id_142d6845` FOREIGN KEY (`group_id`) REFERENCES `auth_group` (`id`);
CREATE INDEX `dashboards_groupdashboard_bda51c3c` ON `dashboards_groupdashboard` (`group_id`);
