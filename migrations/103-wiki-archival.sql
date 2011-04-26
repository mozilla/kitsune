-- Add is_archived flag to wiki documents:
ALTER TABLE wiki_document ADD is_archived bool NOT NULL;
CREATE INDEX `wiki_document_42e00a51` ON `wiki_document` (`is_archived`);

-- And a permission to control it:
INSERT INTO auth_permission (name, content_type_id, codename) VALUES ('Can archive document', (SELECT id FROM django_content_type WHERE app_label='wiki' AND model='document'), 'archive_document');
