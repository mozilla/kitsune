import django.dispatch

tag_added = django.dispatch.Signal(providing_args=['question_id', 'tag_name'])
