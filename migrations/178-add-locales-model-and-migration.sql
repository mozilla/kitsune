CREATE TABLE `wiki_locale_leaders` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `locale_id` integer NOT NULL,
    `user_id` integer NOT NULL,
    UNIQUE (`locale_id`, `user_id`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `wiki_locale_leaders` ADD CONSTRAINT `user_id_refs_id_e961639` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

CREATE TABLE `wiki_locale_reviewers` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `locale_id` integer NOT NULL,
    `user_id` integer NOT NULL,
    UNIQUE (`locale_id`, `user_id`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `wiki_locale_reviewers` ADD CONSTRAINT `user_id_refs_id_590fc64b` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

CREATE TABLE `wiki_locale_editors` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `locale_id` integer NOT NULL,
    `user_id` integer NOT NULL,
    UNIQUE (`locale_id`, `user_id`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `wiki_locale_editors` ADD CONSTRAINT `user_id_refs_id_5b30f591` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);

CREATE TABLE `wiki_locale` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `locale` varchar(7) NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;
ALTER TABLE `wiki_locale_leaders` ADD CONSTRAINT `locale_id_refs_id_e2c5fe94` FOREIGN KEY (`locale_id`) REFERENCES `wiki_locale` (`id`);
ALTER TABLE `wiki_locale_reviewers` ADD CONSTRAINT `locale_id_refs_id_1f5e3d0` FOREIGN KEY (`locale_id`) REFERENCES `wiki_locale` (`id`);
ALTER TABLE `wiki_locale_editors` ADD CONSTRAINT `locale_id_refs_id_c998d4c4` FOREIGN KEY (`locale_id`) REFERENCES `wiki_locale` (`id`);
CREATE INDEX `wiki_locale_928541cb` ON `wiki_locale` (`locale`);

INSERT INTO `wiki_locale` (`locale`) VALUES ('ach');
INSERT INTO `wiki_locale` (`locale`) VALUES ('ak');
INSERT INTO `wiki_locale` (`locale`) VALUES ('ar');
INSERT INTO `wiki_locale` (`locale`) VALUES ('as');
INSERT INTO `wiki_locale` (`locale`) VALUES ('ast');
INSERT INTO `wiki_locale` (`locale`) VALUES ('be');
INSERT INTO `wiki_locale` (`locale`) VALUES ('bg');
INSERT INTO `wiki_locale` (`locale`) VALUES ('bn-BD');
INSERT INTO `wiki_locale` (`locale`) VALUES ('bn-IN');
INSERT INTO `wiki_locale` (`locale`) VALUES ('bs');
INSERT INTO `wiki_locale` (`locale`) VALUES ('ca');
INSERT INTO `wiki_locale` (`locale`) VALUES ('cs');
INSERT INTO `wiki_locale` (`locale`) VALUES ('da');
INSERT INTO `wiki_locale` (`locale`) VALUES ('de');
INSERT INTO `wiki_locale` (`locale`) VALUES ('el');
INSERT INTO `wiki_locale` (`locale`) VALUES ('en-US');
INSERT INTO `wiki_locale` (`locale`) VALUES ('eo');
INSERT INTO `wiki_locale` (`locale`) VALUES ('es');
INSERT INTO `wiki_locale` (`locale`) VALUES ('et');
INSERT INTO `wiki_locale` (`locale`) VALUES ('eu');
INSERT INTO `wiki_locale` (`locale`) VALUES ('fa');
INSERT INTO `wiki_locale` (`locale`) VALUES ('ff');
INSERT INTO `wiki_locale` (`locale`) VALUES ('fi');
INSERT INTO `wiki_locale` (`locale`) VALUES ('fr');
INSERT INTO `wiki_locale` (`locale`) VALUES ('fur');
INSERT INTO `wiki_locale` (`locale`) VALUES ('fy-NL');
INSERT INTO `wiki_locale` (`locale`) VALUES ('ga-IE');
INSERT INTO `wiki_locale` (`locale`) VALUES ('gd');
INSERT INTO `wiki_locale` (`locale`) VALUES ('gl');
INSERT INTO `wiki_locale` (`locale`) VALUES ('gu-IN');
INSERT INTO `wiki_locale` (`locale`) VALUES ('he');
INSERT INTO `wiki_locale` (`locale`) VALUES ('hi-IN');
INSERT INTO `wiki_locale` (`locale`) VALUES ('hr');
INSERT INTO `wiki_locale` (`locale`) VALUES ('hu');
INSERT INTO `wiki_locale` (`locale`) VALUES ('hy-AM');
INSERT INTO `wiki_locale` (`locale`) VALUES ('id');
INSERT INTO `wiki_locale` (`locale`) VALUES ('ilo');
INSERT INTO `wiki_locale` (`locale`) VALUES ('is');
INSERT INTO `wiki_locale` (`locale`) VALUES ('it');
INSERT INTO `wiki_locale` (`locale`) VALUES ('ja');
INSERT INTO `wiki_locale` (`locale`) VALUES ('kk');
INSERT INTO `wiki_locale` (`locale`) VALUES ('km');
INSERT INTO `wiki_locale` (`locale`) VALUES ('kn');
INSERT INTO `wiki_locale` (`locale`) VALUES ('ko');
INSERT INTO `wiki_locale` (`locale`) VALUES ('lg');
INSERT INTO `wiki_locale` (`locale`) VALUES ('lt');
INSERT INTO `wiki_locale` (`locale`) VALUES ('mai');
INSERT INTO `wiki_locale` (`locale`) VALUES ('mk');
INSERT INTO `wiki_locale` (`locale`) VALUES ('ml');
INSERT INTO `wiki_locale` (`locale`) VALUES ('mn');
INSERT INTO `wiki_locale` (`locale`) VALUES ('mr');
INSERT INTO `wiki_locale` (`locale`) VALUES ('ms');
INSERT INTO `wiki_locale` (`locale`) VALUES ('my');
INSERT INTO `wiki_locale` (`locale`) VALUES ('nb-NO');
INSERT INTO `wiki_locale` (`locale`) VALUES ('ne-NP');
INSERT INTO `wiki_locale` (`locale`) VALUES ('nl');
INSERT INTO `wiki_locale` (`locale`) VALUES ('no');
INSERT INTO `wiki_locale` (`locale`) VALUES ('nso');
INSERT INTO `wiki_locale` (`locale`) VALUES ('pa-IN');
INSERT INTO `wiki_locale` (`locale`) VALUES ('pl');
INSERT INTO `wiki_locale` (`locale`) VALUES ('pt-BR');
INSERT INTO `wiki_locale` (`locale`) VALUES ('pt-PT');
INSERT INTO `wiki_locale` (`locale`) VALUES ('rm');
INSERT INTO `wiki_locale` (`locale`) VALUES ('ro');
INSERT INTO `wiki_locale` (`locale`) VALUES ('ru');
INSERT INTO `wiki_locale` (`locale`) VALUES ('rw');
INSERT INTO `wiki_locale` (`locale`) VALUES ('si');
INSERT INTO `wiki_locale` (`locale`) VALUES ('sk');
INSERT INTO `wiki_locale` (`locale`) VALUES ('sl');
INSERT INTO `wiki_locale` (`locale`) VALUES ('son');
INSERT INTO `wiki_locale` (`locale`) VALUES ('sq');
INSERT INTO `wiki_locale` (`locale`) VALUES ('sr-CYRL');
INSERT INTO `wiki_locale` (`locale`) VALUES ('sr-LATN');
INSERT INTO `wiki_locale` (`locale`) VALUES ('sv');
INSERT INTO `wiki_locale` (`locale`) VALUES ('ta-LK');
INSERT INTO `wiki_locale` (`locale`) VALUES ('ta');
INSERT INTO `wiki_locale` (`locale`) VALUES ('te');
INSERT INTO `wiki_locale` (`locale`) VALUES ('th');
INSERT INTO `wiki_locale` (`locale`) VALUES ('tr');
INSERT INTO `wiki_locale` (`locale`) VALUES ('uk');
INSERT INTO `wiki_locale` (`locale`) VALUES ('vi');
INSERT INTO `wiki_locale` (`locale`) VALUES ('zh-CN');
INSERT INTO `wiki_locale` (`locale`) VALUES ('zh-TW');
INSERT INTO `wiki_locale` (`locale`) VALUES ('zu');

