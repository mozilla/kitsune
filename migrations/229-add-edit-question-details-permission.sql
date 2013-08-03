SET @ct = (SELECT id from django_content_type WHERE name='question' AND app_label='questions');

INSERT INTO auth_permission (`name`, `content_type_id`, `codename`) VALUES
    ('Can edit the product and topic of a question', @ct, 'edit_details');
