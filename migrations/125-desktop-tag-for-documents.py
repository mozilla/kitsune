SET @ct = (SELECT id from django_content_type WHERE name='document' AND app_label='wiki');
SET @tag = (SELECT id FROM taggit_tag WHERE name = 'desktop');

INSERT INTO taggit_taggeditem (tag_id, object_id, content_type_id)
    SELECT DISTINCT @tag, document_id, @ct FROM wiki_firefoxversion WHERE item_id IN (1,2,3,5,6,9)
    UNION
    SELECT DISTINCT @tag, document_id, @ct FROM wiki_operatingsystem WHERE item_id IN (1,2,3);
