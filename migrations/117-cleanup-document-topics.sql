SET @ct = (SELECT id from django_content_type WHERE name='document' AND app_label='wiki');
SET @tag = (SELECT id from taggit_tag WHERE name='mobile');

DELETE FROM taggit_taggeditem WHERE tag_id != @tag AND content_type_id = @ct;
