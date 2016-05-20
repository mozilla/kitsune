-- Drop Tiki tables resurrected during the move to PHX.

DROP TABLE IF EXISTS events_event;
DROP TABLE IF EXISTS events_signup;
DROP TABLE IF EXISTS galaxia_activities;
DROP TABLE IF EXISTS galaxia_activity_roles;
DROP TABLE IF EXISTS galaxia_instance_activities;
DROP TABLE IF EXISTS galaxia_instance_comments;
DROP TABLE IF EXISTS galaxia_instances;
DROP TABLE IF EXISTS galaxia_processes;
DROP TABLE IF EXISTS galaxia_roles;
DROP TABLE IF EXISTS galaxia_transitions;
DROP TABLE IF EXISTS galaxia_user_roles;
DROP TABLE IF EXISTS galaxia_workitems;
DROP TABLE IF EXISTS messu_archive;
DROP TABLE IF EXISTS messu_messages;
DROP TABLE IF EXISTS messu_sent;
DROP TABLE IF EXISTS metrics_assigned;
DROP TABLE IF EXISTS metrics_metric;
DROP TABLE IF EXISTS metrics_tab;
DROP TABLE IF EXISTS se_weights;
DROP TABLE IF EXISTS users_grouppermissions;
DROP TABLE IF EXISTS users_groups;
DROP TABLE IF EXISTS users_objectpermissions;
DROP TABLE IF EXISTS users_permissions;
DROP TABLE IF EXISTS users_usergroups;
DROP TABLE IF EXISTS users_users;

-- While we're dropping tables...

DROP TABLE IF EXISTS wiki_helpfulvoteold;
