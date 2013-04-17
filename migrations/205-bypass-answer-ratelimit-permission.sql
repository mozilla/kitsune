SET @ct = (SELECT id from django_content_type WHERE name='answer' AND app_label='questions');

INSERT INTO auth_permission (`name`, `content_type_id`, `codename`) VALUES
    ('Can bypass answering ratelimit', @ct, 'bypass_answer_ratelimit');
