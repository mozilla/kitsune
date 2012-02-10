insert into kpi_metrickind (code) values
    ('search clickthroughs:sphinx:clicks'),
    ('search clickthroughs:sphinx:searches'),
    ('search clickthroughs:elastic:searches'),
    ('search clickthroughs:elastic:clicks');

insert ignore into django_content_type (name, app_label, model) values
    ('metric', 'kpi', 'metric');
insert into auth_permission (name, content_type_id, codename) values ('Can add metric value', (select id from django_content_type where app_label='kpi' and model='metric'), 'add_metric');
