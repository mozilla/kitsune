-- Delete the flag.
DELETE FROM waffle_flag where name='new-topics';

-- Drop the M2M table.
DROP TABLE wiki_document_topics;
