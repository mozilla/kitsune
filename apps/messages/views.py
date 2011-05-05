import jingo
from waffle.decorators import waffle_flag

from access.decorators import login_required
from messages.models import InboxMessage
from sumo.utils import paginate


@waffle_flag('private-messaging')
@login_required
def inbox(request):
    messages = InboxMessage.objects.filter(to=request.user).order_by('-created')
    return jingo.render(request, 'messages/inbox.html',
                        {'mymessages': messages})


@waffle_flag('private-messaging')
@login_required
def read(request, msgid):
    message = InboxMessage.objects.get(pk=msgid, to=request.user)
    was_new = message.unread
    message.read = True
    message.save()
    return jingo.render(request, 'messages/read.html',
                        {'message': message, 'was_new': was_new})
