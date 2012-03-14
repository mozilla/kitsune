CREATE TABLE `karma_points` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `action` varchar(100) NOT NULL UNIQUE,
    `points` integer NOT NULL,
    `updated` datetime NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;
