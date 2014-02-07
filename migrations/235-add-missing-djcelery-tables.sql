CREATE TABLE `celery_taskmeta` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `task_id` varchar(255) NOT NULL UNIQUE,
    `status` varchar(50) NOT NULL,
    `result` longtext,
    `date_done` datetime NOT NULL,
    `traceback` longtext,
    `hidden` bool NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

CREATE TABLE `celery_tasksetmeta` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `taskset_id` varchar(255) NOT NULL UNIQUE,
    `result` longtext NOT NULL,
    `date_done` datetime NOT NULL,
    `hidden` bool NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

CREATE INDEX `celery_taskmeta_2ff6b945` ON `celery_taskmeta` (`hidden`);
CREATE INDEX `celery_tasksetmeta_2ff6b945` ON `celery_tasksetmeta` (`hidden`);
