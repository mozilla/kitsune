-- Clear "ready" flag for typo-significance changes:
UPDATE wiki_revision SET is_ready_for_localization=FALSE WHERE significance<20;

-- ...and on non-English articles:
UPDATE wiki_revision SET is_ready_for_localization=FALSE WHERE document_id NOT IN (SELECT id from wiki_document where locale='en-US');
