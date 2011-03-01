-- Remove surrogate key, and use tweet ID instead. Make reply_to a foreign key,
-- and rename it to conform to our conventions.
ALTER TABLE customercare_tweet DROP id, ADD PRIMARY KEY (tweet_id);
ALTER TABLE customercare_tweet CHANGE reply_to reply_to_id bigint;
ALTER TABLE customercare_tweet ADD CONSTRAINT reply_to_id_refs_tweet_id_47b7f44d FOREIGN KEY (reply_to_id) REFERENCES customercare_tweet (tweet_id);

-- Drop old tweet_id index, now redundant with pkey:
ALTER TABLE customercare_tweet DROP KEY tweet_id;
