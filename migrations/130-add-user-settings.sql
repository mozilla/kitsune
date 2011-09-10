CREATE TABLE `users_setting` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer NOT NULL,
    `name` varchar(100) NOT NULL,
    `value` varchar(60) NOT NULL,
    UNIQUE (`user_id`, `name`)
)
;
ALTER TABLE `users_setting` ADD CONSTRAINT `user_id_refs_id_3bbb02c4` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE INDEX `users_setting_403f60f` ON `users_setting` (`user_id`);

