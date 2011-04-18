CREATE TABLE `messages_inboxmessage` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `to_id` integer NOT NULL,
    `sender_id` integer,
    `message` longtext NOT NULL,
    `created` datetime NOT NULL,
    `read` bool NOT NULL,
    `replied` bool NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci
;
ALTER TABLE `messages_inboxmessage` ADD CONSTRAINT `to_id_refs_id_2d90390f` FOREIGN KEY (`to_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `messages_inboxmessage` ADD CONSTRAINT `sender_id_refs_id_2d90390f` FOREIGN KEY (`sender_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `messages_outboxmessage_to` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `outboxmessage_id` integer NOT NULL,
    `user_id` integer NOT NULL,
    UNIQUE (`outboxmessage_id`, `user_id`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci
;
ALTER TABLE `messages_outboxmessage_to` ADD CONSTRAINT `user_id_refs_id_de0b949e` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE TABLE `messages_outboxmessage` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `sender_id` integer NOT NULL,
    `message` longtext NOT NULL,
    `created` datetime NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci
;
ALTER TABLE `messages_outboxmessage` ADD CONSTRAINT `sender_id_refs_id_4fcca07f` FOREIGN KEY (`sender_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `messages_outboxmessage_to` ADD CONSTRAINT `outboxmessage_id_refs_id_f8c08fc4` FOREIGN KEY (`outboxmessage_id`) REFERENCES `messages_outboxmessage` (`id`);
CREATE INDEX `messages_inboxmessage_80e39a0d` ON `messages_inboxmessage` (`to_id`);
CREATE INDEX `messages_inboxmessage_901f59e9` ON `messages_inboxmessage` (`sender_id`);
CREATE INDEX `messages_inboxmessage_3216ff68` ON `messages_inboxmessage` (`created`);
CREATE INDEX `messages_inboxmessage_df3d2e75` ON `messages_inboxmessage` (`read`);
CREATE INDEX `messages_outboxmessage_901f59e9` ON `messages_outboxmessage` (`sender_id`);
CREATE INDEX `messages_outboxmessage_3216ff68` ON `messages_outboxmessage` (`created`);
