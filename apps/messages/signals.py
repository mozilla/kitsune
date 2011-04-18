import django.dispatch


message_sent = django.dispatch.Signal(providing_args=['to', 'text',
                                                      'msg_sender'])
