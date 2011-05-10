from django.contrib import messages as contrib_messages
from django.http import HttpResponseRedirect

import jingo
from tower import ugettext as _
from waffle.decorators import waffle_flag

from access.decorators import login_required
from messages import send_message
from messages.forms import MessageForm, ReplyForm
from messages.models import InboxMessage, OutboxMessage
from sumo.urlresolvers import reverse
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
    if message.unread:
        message.read = True
        message.save()
    form = ReplyForm(initial={'to': message.sender})
    return jingo.render(request, 'messages/read.html',
                        {'message': message, 'form': form})


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


@waffle_flag('private-messaging')
@login_required
def new_message(request):
    form = MessageForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        send_message(form.cleaned_data['to'], form.cleaned_data['message'],
                     request.user)
        contrib_messages.add_message(request, contrib_messages.SUCCESS,
                                     _('Your message was sent!'))
        return HttpResponseRedirect(reverse('messages.inbox'))

    return jingo.render(request, 'messages/new.html', {'form': form})
