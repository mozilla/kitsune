import jingo
from waffle.decorators import waffle_flag

from access.decorators import login_required
from messages.models import InboxMessage, OutboxMessage
from sumo.utils import paginate


@waffle_flag('private-messaging')
@login_required
def inbox(request):
    user = request.user
    messages = InboxMessage.objects.filter(to=user).order_by('-created')
    return jingo.render(request, 'messages/inbox.html',
                        {'msgs': messages})


@waffle_flag('private-messaging')
@login_required
def read(request, msgid):
    message = InboxMessage.objects.get(pk=msgid, to=request.user)
    was_new = message.unread
    message.read = True
    message.save()
    return jingo.render(request, 'messages/read.html',
                        {'message': message, 'was_new': was_new})


@waffle_flag('private-messaging')
@login_required
def outbox(request):
    user = request.user
    messages = OutboxMessage.objects.filter(sender=user).order_by('-created')
    for msg in messages:
        msg.recipients = msg.to.count()
        if msg.recipients == 1:
            msg.recipient = msg.to.all()[0]
    return jingo.render(request, 'messages/outbox.html',
                        {'msgs': messages})
