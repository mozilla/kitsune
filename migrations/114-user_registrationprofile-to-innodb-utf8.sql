ALTER TABLE `users_registrationprofile` ENGINE=InnoDB DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;

ALTER TABLE `users_registrationprofile` CHANGE `activation_key` `activation_key` VARCHAR(40) CHARACTER SET utf8 COLLATE utf8_general_ci NOT NULL;