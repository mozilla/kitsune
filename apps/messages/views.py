import json

from django.contrib import messages as contrib_messages
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404

import jingo
from multidb.pinning import mark_as_write
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
    messages = InboxMessage.uncached.filter(to=user).order_by('-created')
    return jingo.render(request, 'messages/inbox.html',
                        {'msgs': messages})


@waffle_flag('private-messaging')
@login_required
def read(request, msgid):
    message = get_object_or_404(InboxMessage, pk=msgid, to=request.user)
    was_new = message.unread
    if was_new:
        message.update(read=True)
    initial = {'to': message.sender, 'in_reply_to': message.pk}
    form = ReplyForm(initial=initial)
    response = jingo.render(request, 'messages/read.html',
                            {'message': message, 'form': form})
    if was_new:
        response = mark_as_write(response)
    return response


@waffle_flag('private-messaging')
@login_required
def read_outbox(request, msgid):
    message = get_object_or_404(OutboxMessage, pk=msgid, sender=request.user)
    return jingo.render(request, 'messages/read-outbox.html',
                        {'message': _add_recipients(message)})


@waffle_flag('private-messaging')
@login_required
def outbox(request):
    user = request.user
    messages = OutboxMessage.uncached.filter(sender=user).order_by('-created')
    for msg in messages:
        _add_recipients(msg)
    return jingo.render(request, 'messages/outbox.html',
                        {'msgs': messages})


@waffle_flag('private-messaging')
@login_required
def new_message(request):
    """Send a new private message."""
    to = request.GET.get('to')
    if to:
        try:
            User.objects.get(username=to)
        except User.DoesNotExist:
            contrib_messages.add_message(
                request, contrib_messages.ERROR,
                _('Invalid username provided. Enter a new username below.'))
            return HttpResponseRedirect(reverse('messages.new'))

    form = MessageForm(request.POST or None, initial={'to': to})

    if request.method == 'POST' and form.is_valid():
        send_message(form.cleaned_data['to'], form.cleaned_data['message'],
                     request.user)
        if form.cleaned_data['in_reply_to']:
            irt = form.cleaned_data['in_reply_to']
            try:
                m = InboxMessage.objects.get(pk=irt, to=request.user)
                m.update(replied=True)
            except InboxMessage.DoesNotExist:
                pass
        contrib_messages.add_message(request, contrib_messages.SUCCESS,
                                     _('Your message was sent!'))
        return HttpResponseRedirect(reverse('messages.inbox'))

    return jingo.render(request, 'messages/new.html', {'form': form})


@waffle_flag('private-messaging')
@login_required
def delete(request, msgid, msgtype='inbox'):
    if msgtype == 'inbox':
        message = get_object_or_404(InboxMessage, pk=msgid, to=request.user)
    else:
        message = get_object_or_404(OutboxMessage, pk=msgid,
                                    sender=request.user)

    if request.method == 'POST':
        message.delete()
        msg = _('The message was deleted!')

        if request.is_ajax():
            return HttpResponse(json.dumps({'message': message}))

        contrib_messages.add_message(request, contrib_messages.SUCCESS, msg)
        return HttpResponseRedirect(reverse('messages.{t}'.format(t=msgtype)))

    if msgtype == 'outbox':
        _add_recipients(message)

    return jingo.render(request, 'messages/delete.html',
                        {'message': message, 'msgtype': msgtype})


def _add_recipients(msg):
    msg.recipients = msg.to.count()
    if msg.recipients == 1:
        msg.recipient = msg.to.all()[0]
    return msg
