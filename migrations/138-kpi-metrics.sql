CREATE TABLE `kpi_metrickind` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `code` varchar(255) NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

CREATE TABLE `kpi_metric` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `kind_id` integer NOT NULL,
    `start` date NOT NULL,
    `end` date NOT NULL,
    `value` integer UNSIGNED NOT NULL,
    UNIQUE (`kind_id`, `start`, `end`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

ALTER TABLE `kpi_metric` ADD CONSTRAINT `kind_id_refs_id_8a165d49` FOREIGN KEY (`kind_id`) REFERENCES `kpi_metrickind` (`id`);
CREATE INDEX `kpi_metrickind_65da3d2c` ON `kpi_metrickind` (`code`);
