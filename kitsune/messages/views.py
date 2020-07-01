import json

from django.contrib import messages as contrib_messages
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from django.views.decorators.http import require_POST
from multidb.pinning import mark_as_write

from kitsune.access.decorators import login_required
from kitsune.messages import MESSAGES_PER_PAGE
from kitsune.messages.forms import MessageForm
from kitsune.messages.forms import ReplyForm
from kitsune.messages.models import InboxMessage
from kitsune.messages.models import OutboxMessage
from kitsune.messages.utils import send_message
from kitsune.sumo.urlresolvers import reverse
from kitsune.sumo.utils import is_ratelimited
from kitsune.sumo.utils import paginate


@login_required
def inbox(request):
    user = request.user
    messages = InboxMessage.objects.filter(to=user).order_by('-created')
    count = messages.count()

    messages = paginate(
        request, messages, per_page=MESSAGES_PER_PAGE, count=count)

    return render(request, 'messages/inbox.html', {'msgs': messages})


@login_required
def read(request, msgid):
    message = get_object_or_404(InboxMessage, pk=msgid, to=request.user)
    was_new = message.unread
    if was_new:
        message.update(read=True)
    initial = {'to': message.sender, 'in_reply_to': message.pk}
    form = ReplyForm(initial=initial)
    response = render(request, 'messages/read.html', {
        'message': message, 'form': form})
    if was_new:
        response = mark_as_write(response)
    return response


@login_required
def read_outbox(request, msgid):
    message = get_object_or_404(OutboxMessage, pk=msgid, sender=request.user)
    return render(request, 'messages/read-outbox.html', {
        'message': _add_recipients(message)})


@login_required
def outbox(request):
    user = request.user
    messages = OutboxMessage.objects.filter(sender=user).order_by('-created')
    count = messages.count()

    messages = paginate(
        request, messages, per_page=MESSAGES_PER_PAGE, count=count)

    for msg in messages.object_list:
        _add_recipients(msg)

    return render(request, 'messages/outbox.html', {'msgs': messages})


@login_required
def new_message(request):
    """Send a new private message."""
    to = request.GET.get('to')
    if to:
        try:
            for username in to.split(','):
                User.objects.get(username=username)
        except User.DoesNotExist:
            contrib_messages.add_message(
                request, contrib_messages.ERROR,
                _('Invalid username provided. Enter a new username below.'))
            return HttpResponseRedirect(reverse('messages.new'))

    message = request.GET.get('message')

    form = MessageForm(request.POST or None, initial={'to': to, 'message': message})

    if (request.method == 'POST' and form.is_valid() and
            not is_ratelimited(request, 'primate-message-day', '50/d')):
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

    return render(request, 'messages/new.html', {'form': form})


@login_required
def bulk_action(request, msgtype='inbox'):
    """Apply action to selected messages."""
    msgids = request.POST.getlist('id')

    if len(msgids) == 0:
        contrib_messages.add_message(request, contrib_messages.ERROR,
                                     _("No messages selected. Please try again."))
    else:
        if 'delete' in request.POST:
            return delete(request, msgtype=msgtype)
        elif 'mark_read' in request.POST and msgtype == 'inbox':
            messages = InboxMessage.objects.filter(pk__in=msgids,
                                                   to=request.user)
            messages.update(read=True)
        elif 'mark_unread' in request.POST and msgtype == 'inbox':
            messages = InboxMessage.objects.filter(pk__in=msgids,
                                                   to=request.user)
            messages.update(read=False)

    return redirect('messages.%s' % msgtype)


@login_required
def delete(request, msgid=None, msgtype='inbox'):
    if msgid:
        msgids = [msgid]
    else:
        try:
            msgids = [int(m) for m in request.POST.getlist('id')]
        except ValueError:
            return HttpResponseBadRequest()

    if msgtype == 'inbox':
        messages = InboxMessage.objects.filter(pk__in=msgids, to=request.user)
    else:
        messages = OutboxMessage.objects.filter(pk__in=msgids,
                                                sender=request.user)

    if request.method == 'POST' and 'confirmed' in request.POST:
        if messages.count() != len(msgids):
            contrib_messages.add_message(request, contrib_messages.ERROR,
                                         _("Messages didn't add up. Try again."))
        else:
            messages.delete()
            msg = ungettext('The message was deleted!',
                            'The messages were deleted!',
                            len(msgids))
            contrib_messages.add_message(request, contrib_messages.SUCCESS,
                                         msg)

        if request.is_ajax():
            return HttpResponse(json.dumps({'message': m} for m in messages))

        return HttpResponseRedirect(reverse('messages.{t}'.format(t=msgtype)))

    if msgtype == 'outbox':
        for message in messages:
            _add_recipients(message)

    return render(request, 'messages/delete.html', {
        'msgs': messages, 'msgid': msgid, 'msgtype': msgtype})


@require_POST
@login_required
def preview_async(request):
    """Ajax preview of posts."""
    m = OutboxMessage(sender=request.user,
                      message=request.POST.get('content', ''))
    return render(request, 'messages/includes/message_preview.html', {
        'message': m})


def _add_recipients(msg):
    msg.recipients = msg.to.count()
    if msg.recipients == 1:
        msg.recipient = msg.to.all()[0]
    else:
        msg.recipient = None
    return msg
