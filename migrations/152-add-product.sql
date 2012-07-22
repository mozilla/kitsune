CREATE TABLE `products_product` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `title` varchar(255) NOT NULL,
    `description` longtext NOT NULL,
    `display_order` integer NOT NULL,
    `visible` bool NOT NULL,
    `slug` varchar(50) NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

CREATE INDEX `products_product_7be581d8` ON `products_product` (`title`);
CREATE INDEX `products_product_56ae2a2a` ON `products_product` (`slug`);

INSERT INTO `django_content_type` (`name`, `app_label`, `model`) VALUES ('product','products','product');

SELECT (@id:=`id`) FROM `django_content_type` WHERE `name` = 'product';

INSERT INTO `auth_permission` (`name`, `content_type_id`, `codename`) VALUES ('Can add product',@id,'add_product'),('Can change product',@id,'change_product'),('Can delete product',@id,'delete_product');


