-- Add an `allow_discussion` column to wiki_document.
ALTER TABLE wiki_document
    ADD COLUMN allow_discussion TINYINT(1) NOT NULL DEFAULT 1;
