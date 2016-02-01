from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.db.models.loading import get_model
from django.utils.translation import ugettext as _
from django.template.context import RequestContext
from django.template import loader
from django.contrib.auth.decorators import login_required

from authority.models import Permission
from authority.forms import UserPermissionForm
from authority.templatetags.permissions import url_for_obj


def get_next(request, obj=None):
    next = request.REQUEST.get('next')
    if not next:
        if obj and hasattr(obj, 'get_absolute_url'):
            next = obj.get_absolute_url()
        else:
            next = '/'
    return next


@login_required
def add_permission(request, app_label, module_name, pk, approved=False,
                   template_name='authority/permission_form.html',
                   extra_context=None, form_class=UserPermissionForm):
    codename = request.POST.get('codename', None)
    model = get_model(app_label, module_name)
    if model is None:
        return permission_denied(request)
    obj = get_object_or_404(model, pk=pk)
    next = get_next(request, obj)
    if approved:
        if not request.user.has_perm('authority.add_permission'):
            return HttpResponseRedirect(
                url_for_obj('authority-add-permission-request', obj))
        view_name = 'authority-add-permission'
    else:
        view_name = 'authority-add-permission-request'
    if request.method == 'POST':
        if codename is None:
            return HttpResponseForbidden(next)
        form = form_class(data=request.POST, obj=obj, approved=approved,
                          perm=codename, initial=dict(codename=codename))
        if not approved:
            # Limit permission request to current user
            form.data['user'] = request.user
        if form.is_valid():
            request.user.message_set.create(
                message=_('You added a permission request.'))
            return HttpResponseRedirect(next)
    else:
        form = form_class(obj=obj, approved=approved, perm=codename,
                          initial=dict(codename=codename))
    context = {
        'form': form,
        'form_url': url_for_obj(view_name, obj),
        'next': next,
        'perm': codename,
        'approved': approved,
    }
    if extra_context:
        context.update(extra_context)
    return render_to_response(template_name, context,
                              context_instance=RequestContext(request))


@login_required
def approve_permission_request(request, permission_pk):
    requested_permission = get_object_or_404(Permission, pk=permission_pk)
    if request.user.has_perm('authority.approve_permission_requests'):
        requested_permission.approve(request.user)
        request.user.message_set.create(
            message=_('You approved the permission request.'))
    next = get_next(request, requested_permission)
    return HttpResponseRedirect(next)


@login_required
def delete_permission(request, permission_pk, approved):
    permission = get_object_or_404(Permission,  pk=permission_pk,
                                   approved=approved)
    if (request.user.has_perm('authority.delete_foreign_permissions') or
            request.user == permission.creator):
        permission.delete()
        if approved:
            msg = _('You removed the permission.')
        else:
            msg = _('You removed the permission request.')
        request.user.message_set.create(message=msg)
    next = get_next(request)
    return HttpResponseRedirect(next)


def permission_denied(request, template_name=None, extra_context=None):
    """
    Default 403 handler.

    Templates: `403.html`
    Context:
        request_path
            The path of the requested URL (e.g., '/app/pages/bad_page/')
    """
    if template_name is None:
        template_name = ('403.html', 'authority/403.html')
    context = {
        'request_path': request.path,
    }
    if extra_context:
        context.update(extra_context)
    return HttpResponseForbidden(loader.render_to_string(template_name, context,
                                 context_instance=RequestContext(request)))
