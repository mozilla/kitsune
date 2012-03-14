CREATE TABLE `customercare_reply` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_id` integer,
    `twitter_username` varchar(20) NOT NULL,
    `tweet_id` bigint NOT NULL,
    `raw_json` longtext NOT NULL,
    `locale` varchar(20) NOT NULL,
    `created` datetime NOT NULL,
    `reply_to_tweet_id` bigint NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

ALTER TABLE `customercare_reply` ADD CONSTRAINT `user_id_refs_id_e32e21e0` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
CREATE INDEX `customercare_reply_fbfc09f1` ON `customercare_reply` (`user_id`);
CREATE INDEX `customercare_reply_3216ff68` ON `customercare_reply` (`created`);

INSERT INTO django_content_type (`name`, `app_label`, `model`) VALUES
    ('reply', 'customercare', 'reply');
SET @ct = LAST_INSERT_ID();
INSERT INTO auth_permission (`name`, `content_type_id`, `codename`) VALUES
    ('Can add reply', @ct, 'add_reply'),
    ('Can change reply', @ct, 'change_reply'),
    ('Can delete reply', @ct, 'delete_reply');
