SELECT (@flagid:=`id`) FROM `waffle_flag` WHERE `name`='new-theme';

DELETE FROM `waffle_flag_groups` where `flag_id`=@flagid;
DELETE FROM `waffle_flag_users` where `flag_id`=@flagid;
DELETE FROM `waffle_flag` where `id`=@flagid;
