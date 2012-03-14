CREATE TABLE `search_record` (
    `id` integer AUTO_INCREMENT NOT NULL PRIMARY KEY,
    `starttime` datetime,
    `endtime` datetime,
    `text` varchar(255) NOT NULL
) ENGINE=InnoDB CHARACTER SET utf8 COLLATE utf8_general_ci;

INSERT INTO django_content_type (name, app_label, model) VALUES
    ('record', 'search', 'record');
SET @ct = (SELECT id from django_content_type WHERE app_label='search' and model='record');
INSERT INTO auth_permission (name, content_type_id, codename) VALUES
    ('Can add record', @ct, 'add_record'),
    ('Can change record', @ct, 'change_record'),
    ('Can delete record', @ct, 'delete_record'),
    ('Can run a full reindexing', @ct, 'reindex');
