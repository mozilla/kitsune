-- Make sure NOT NULL columns are not NULL.
UPDATE waffle_flag SET created = NOW(), modified = NOW();
UPDATE waffle_switch SET created = NOW(), modified = NOW();
UPDATE waffle_sample SET created = NOW(), modified = NOW();
