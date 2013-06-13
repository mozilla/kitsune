-- Create new model.
CREATE TABLE `products_topic` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `title` varchar(255) NOT NULL,
    `slug` varchar(255) NOT NULL,
    `description` longtext NOT NULL,
    `image` varchar(250),
    `product_id` integer NOT NULL,
    `parent_id` integer,
    `display_order` integer NOT NULL,
    `visible` bool NOT NULL,
    UNIQUE (`slug`, `product_id`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

ALTER TABLE `products_topic` ADD CONSTRAINT `product_id_refs_id_7ce90cf3` FOREIGN KEY (`product_id`) REFERENCES `products_product` (`id`);
ALTER TABLE `products_topic` ADD CONSTRAINT `parent_id_refs_id_2435bae7` FOREIGN KEY (`parent_id`) REFERENCES `products_topic` (`id`);

CREATE INDEX `products_topic_841a7e28` ON `products_topic` (`title`);
CREATE INDEX `products_topic_a951d5d6` ON `products_topic` (`slug`);
CREATE INDEX `products_topic_bb420c12` ON `products_topic` (`product_id`);
CREATE INDEX `products_topic_63f17a16` ON `products_topic` (`parent_id`);


-- Add the content type and permissions.
INSERT INTO `django_content_type` (`name`, `app_label`, `model`) VALUES ('topic','products','topic');
SELECT (@id:=`id`) FROM `django_content_type` WHERE `name` = 'topic' AND `app_label` = 'products';
INSERT INTO `auth_permission` (`name`, `content_type_id`, `codename`) VALUES ('Can add topic',@id,'add_topic'),('Can change topic',@id,'change_topic'),('Can delete topic',@id,'delete_topic');


-- Add the M2M with documents.
CREATE TABLE `wiki_document_new_topics` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `document_id` integer NOT NULL,
    `topic_id` integer NOT NULL,
    UNIQUE (`document_id`, `topic_id`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

ALTER TABLE `wiki_document_new_topics` ADD CONSTRAINT `document_id_refs_id_e73cc77e` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`);
ALTER TABLE `wiki_document_new_topics` ADD CONSTRAINT `topic_id_refs_id_39036d41` FOREIGN KEY (`topic_id`) REFERENCES `products_topic` (`id`);
