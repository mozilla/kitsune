CREATE TABLE `dashboards_wikimetrickind` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `code` varchar(255) NOT NULL UNIQUE
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

CREATE TABLE `dashboards_wikimetric` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `kind_id` integer NOT NULL,
    `locale` varchar(7),
    `product_id` integer,
    `date` date NOT NULL,
    `value` double precision NOT NULL,
    UNIQUE (`kind_id`, `product_id`, `locale`, `date`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

ALTER TABLE `dashboards_wikimetric` ADD CONSTRAINT `kind_id_refs_id_102e3e37` FOREIGN KEY (`kind_id`) REFERENCES `dashboards_wikimetrickind` (`id`);
ALTER TABLE `dashboards_wikimetric` ADD CONSTRAINT `product_id_refs_id_7aaf7d8c` FOREIGN KEY (`product_id`) REFERENCES `products_product` (`id`);
CREATE INDEX `dashboards_wikimetric_e52ac752` ON `dashboards_wikimetric` (`kind_id`);
CREATE INDEX `dashboards_wikimetric_928541cb` ON `dashboards_wikimetric` (`locale`);
CREATE INDEX `dashboards_wikimetric_bb420c12` ON `dashboards_wikimetric` (`product_id`);
