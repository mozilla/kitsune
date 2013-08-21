BEGIN;
CREATE TABLE `badger_badge_prerequisites` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `from_badge_id` integer NOT NULL,
    `to_badge_id` integer NOT NULL,
    UNIQUE (`from_badge_id`, `to_badge_id`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci
;
CREATE TABLE `badger_badge` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `title` varchar(255) NOT NULL UNIQUE,
    `slug` varchar(50) NOT NULL UNIQUE,
    `description` longtext NOT NULL,
    `image` varchar(100),
    `unique` bool NOT NULL,
    `nominations_accepted` bool NOT NULL,
    `nominations_autoapproved` bool NOT NULL,
    `creator_id` integer,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    UNIQUE (`title`, `slug`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci
;
ALTER TABLE `badger_badge` ADD CONSTRAINT `creator_id_refs_id_55558a5` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `badger_badge_prerequisites` ADD CONSTRAINT `from_badge_id_refs_id_d4b9dea9` FOREIGN KEY (`from_badge_id`) REFERENCES `badger_badge` (`id`);
ALTER TABLE `badger_badge_prerequisites` ADD CONSTRAINT `to_badge_id_refs_id_d4b9dea9` FOREIGN KEY (`to_badge_id`) REFERENCES `badger_badge` (`id`);
CREATE TABLE `badger_award` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `description` longtext NOT NULL,
    `badge_id` integer NOT NULL,
    `image` varchar(100),
    `claim_code` varchar(32) NOT NULL,
    `user_id` integer NOT NULL,
    `creator_id` integer,
    `hidden` bool NOT NULL,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci
;
ALTER TABLE `badger_award` ADD CONSTRAINT `user_id_refs_id_5fca6095` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `badger_award` ADD CONSTRAINT `creator_id_refs_id_5fca6095` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `badger_award` ADD CONSTRAINT `badge_id_refs_id_db597ec3` FOREIGN KEY (`badge_id`) REFERENCES `badger_badge` (`id`);
CREATE TABLE `badger_progress` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `badge_id` integer NOT NULL,
    `user_id` integer NOT NULL,
    `percent` double precision NOT NULL,
    `counter` double precision,
    `notes` longtext,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL,
    UNIQUE (`badge_id`, `user_id`)
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci
;
ALTER TABLE `badger_progress` ADD CONSTRAINT `user_id_refs_id_970178b6` FOREIGN KEY (`user_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `badger_progress` ADD CONSTRAINT `badge_id_refs_id_382861f2` FOREIGN KEY (`badge_id`) REFERENCES `badger_badge` (`id`);
CREATE TABLE `badger_deferredaward` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `badge_id` integer NOT NULL,
    `description` longtext NOT NULL,
    `reusable` bool NOT NULL,
    `email` varchar(75),
    `claim_code` varchar(32) NOT NULL UNIQUE,
    `claim_group` varchar(32),
    `creator_id` integer,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci
;
ALTER TABLE `badger_deferredaward` ADD CONSTRAINT `creator_id_refs_id_cd022d20` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `badger_deferredaward` ADD CONSTRAINT `badge_id_refs_id_d6d0b988` FOREIGN KEY (`badge_id`) REFERENCES `badger_badge` (`id`);
CREATE TABLE `badger_nomination` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `badge_id` integer NOT NULL,
    `nominee_id` integer NOT NULL,
    `accepted` bool NOT NULL,
    `creator_id` integer,
    `approver_id` integer,
    `rejected_by_id` integer,
    `rejected_reason` longtext NOT NULL,
    `award_id` integer,
    `created` datetime NOT NULL,
    `modified` datetime NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci
;
ALTER TABLE `badger_nomination` ADD CONSTRAINT `award_id_refs_id_61b52c3` FOREIGN KEY (`award_id`) REFERENCES `badger_award` (`id`);
ALTER TABLE `badger_nomination` ADD CONSTRAINT `nominee_id_refs_id_ddea4883` FOREIGN KEY (`nominee_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `badger_nomination` ADD CONSTRAINT `creator_id_refs_id_ddea4883` FOREIGN KEY (`creator_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `badger_nomination` ADD CONSTRAINT `approver_id_refs_id_ddea4883` FOREIGN KEY (`approver_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `badger_nomination` ADD CONSTRAINT `rejected_by_id_refs_id_ddea4883` FOREIGN KEY (`rejected_by_id`) REFERENCES `auth_user` (`id`);
ALTER TABLE `badger_nomination` ADD CONSTRAINT `badge_id_refs_id_198f0255` FOREIGN KEY (`badge_id`) REFERENCES `badger_badge` (`id`);
CREATE INDEX `badger_badge_f97a5119` ON `badger_badge` (`creator_id`);
CREATE INDEX `badger_award_80db5b24` ON `badger_award` (`badge_id`);
CREATE INDEX `badger_award_2b783fbf` ON `badger_award` (`claim_code`);
CREATE INDEX `badger_award_fbfc09f1` ON `badger_award` (`user_id`);
CREATE INDEX `badger_award_f97a5119` ON `badger_award` (`creator_id`);
CREATE INDEX `badger_progress_80db5b24` ON `badger_progress` (`badge_id`);
CREATE INDEX `badger_progress_fbfc09f1` ON `badger_progress` (`user_id`);
CREATE INDEX `badger_deferredaward_80db5b24` ON `badger_deferredaward` (`badge_id`);
CREATE INDEX `badger_deferredaward_3904588a` ON `badger_deferredaward` (`email`);
CREATE INDEX `badger_deferredaward_1185574` ON `badger_deferredaward` (`claim_group`);
CREATE INDEX `badger_deferredaward_f97a5119` ON `badger_deferredaward` (`creator_id`);
CREATE INDEX `badger_nomination_80db5b24` ON `badger_nomination` (`badge_id`);
CREATE INDEX `badger_nomination_2b1dcb5e` ON `badger_nomination` (`nominee_id`);
CREATE INDEX `badger_nomination_f97a5119` ON `badger_nomination` (`creator_id`);
CREATE INDEX `badger_nomination_ca2b68c3` ON `badger_nomination` (`approver_id`);
CREATE INDEX `badger_nomination_f77393ed` ON `badger_nomination` (`rejected_by_id`);
CREATE INDEX `badger_nomination_f98cd8fe` ON `badger_nomination` (`award_id`);
COMMIT;
