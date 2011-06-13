from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_http_methods

import jingo
from tower import ugettext as _

from access.decorators import login_required
from groups.forms import GroupProfileForm
from groups.models import GroupProfile


def list(request):
    groups = GroupProfile.objects.select_related('group').all()
    return jingo.render(request, 'groups/list.html', {'groups': groups})


def profile(request, group_slug):
    prof = get_object_or_404(GroupProfile, slug=group_slug)
    leaders = prof.leaders.all()
    members = prof.group.user_set.all()
    return jingo.render(request, 'groups/profile.html',
                        {'profile': prof, 'leaders': leaders,
                         'members': members})


@login_required
@require_http_methods(['GET', 'POST'])
def edit(request, group_slug):
    prof = get_object_or_404(GroupProfile, slug=group_slug)

    if not (request.user.has_perm('groups.change_groupprofile') or
            request.user in prof.leaders.all()):
        raise PermissionDenied

    form = GroupProfileForm(request.POST or None, instance=prof)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.add_message(request, messages.SUCCESS,
                             _('Group information updated successfully!'))
        return HttpResponseRedirect(prof.get_absolute_url())

    return jingo.render(request, 'groups/edit.html',
                        {'form': form, 'profile': prof})
