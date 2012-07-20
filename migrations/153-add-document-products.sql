CREATE TABLE `wiki_document_products` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `document_id` integer NOT NULL,
    `product_id` integer NOT NULL,
    UNIQUE (`document_id`, `product_id`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;
;
ALTER TABLE `wiki_document_products` ADD CONSTRAINT `product_id_refs_id_6da56fea` FOREIGN KEY (`product_id`) REFERENCES `products_product` (`id`);

ALTER TABLE `wiki_document_products` ADD CONSTRAINT `document_id_refs_id_1680d707` FOREIGN KEY (`document_id`) REFERENCES `wiki_document` (`id`);
