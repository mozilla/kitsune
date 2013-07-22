CREATE TABLE `dashboards_wikimetric` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `code` varchar(255) NOT NULL,
    `locale` varchar(7),
    `product_id` integer,
    `date` date NOT NULL,
    `value` double precision NOT NULL,
    UNIQUE (`code`, `product_id`, `locale`, `date`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

ALTER TABLE `dashboards_wikimetric` ADD CONSTRAINT `product_id_refs_id_7aaf7d8c` FOREIGN KEY (`product_id`) REFERENCES `products_product` (`id`);
CREATE INDEX `dashboards_wikimetric_65da3d2c` ON `dashboards_wikimetric` (`code`);
CREATE INDEX `dashboards_wikimetric_928541cb` ON `dashboards_wikimetric` (`locale`);
CREATE INDEX `dashboards_wikimetric_bb420c12` ON `dashboards_wikimetric` (`product_id`);

INSERT INTO `django_content_type` (`name`, `app_label`, `model`) VALUES ('wikimetric','dashboards','wikimetric');

SELECT (@id:=`id`) FROM `django_content_type` WHERE `name` = 'wikimetric';

INSERT INTO `auth_permission` (`name`, `content_type_id`, `codename`)
	VALUES ('Can add wikimetric',@id,'add_wikimetric'),
		   ('Can change wikimetric',@id,'change_wikimetric'),
		   ('Can delete wikimetric',@id,'delete_wikimetric');
