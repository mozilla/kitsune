CREATE TABLE `axes_accessattempt` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_agent` varchar(255) NOT NULL,
    `ip_address` char(15),
    `username` varchar(255),
    `trusted` bool NOT NULL,
    `http_accept` varchar(1025) NOT NULL,
    `path_info` varchar(255) NOT NULL,
    `attempt_time` datetime NOT NULL,
    `get_data` longtext NOT NULL,
    `post_data` longtext NOT NULL,
    `failures_since_start` integer UNSIGNED NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

CREATE TABLE `axes_accesslog` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `user_agent` varchar(255) NOT NULL,
    `ip_address` char(15),
    `username` varchar(255),
    `trusted` bool NOT NULL,
    `http_accept` varchar(1025) NOT NULL,
    `path_info` varchar(255) NOT NULL,
    `attempt_time` datetime NOT NULL,
    `logout_time` datetime
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;
