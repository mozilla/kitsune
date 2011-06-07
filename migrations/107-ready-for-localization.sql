ALTER TABLE wiki_revision ADD COLUMN is_ready_for_localization boolean NOT NULL DEFAULT true;

ALTER TABLE wiki_document ADD COLUMN latest_localizable_revision_id int AFTER current_revision_id;
ALTER TABLE wiki_document ADD CONSTRAINT latest_localizable_revision_id_refs_id_79f9a479 FOREIGN KEY (latest_localizable_revision_id) REFERENCES wiki_revision (id);
UPDATE wiki_document SET latest_localizable_revision_id=current_revision_id;
