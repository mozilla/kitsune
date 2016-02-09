from django import forms, template
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext, ungettext, ugettext_lazy as _
from django.shortcuts import render_to_response
from django.utils.safestring import mark_safe
from django.forms.formsets import all_valid
from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied

try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text

try:
    from django.contrib.admin import actions
except ImportError:
    actions = False

from authority.models import Permission
from authority.widgets import GenericForeignKeyRawIdWidget
from authority import get_choices_for


class PermissionInline(generic.GenericTabularInline):
    model = Permission
    raw_id_fields = ('user', 'group', 'creator')
    extra = 1

    def formfield_for_dbfield(self, db_field, **kwargs):
        if db_field.name == 'codename':
            perm_choices = get_choices_for(self.parent_model)
            kwargs['label'] = _('permission')
            kwargs['widget'] = forms.Select(choices=perm_choices)
        return super(PermissionInline, self).formfield_for_dbfield(db_field, **kwargs)


class ActionPermissionInline(PermissionInline):
    raw_id_fields = ()
    template = 'admin/edit_inline/action_tabular.html'


class ActionErrorList(forms.utils.ErrorList):
    def __init__(self, inline_formsets):
        for inline_formset in inline_formsets:
            self.extend(inline_formset.non_form_errors())
            for errors_in_inline_form in inline_formset.errors:
                self.extend(errors_in_inline_form.values())


def edit_permissions(modeladmin, request, queryset):
    opts = modeladmin.model._meta
    app_label = opts.app_label

    # Check that the user has the permission to edit permissions
    if not (request.user.is_superuser or
            request.user.has_perm('authority.change_permission') or
            request.user.has_perm('authority.change_foreign_permissions')):
        raise PermissionDenied

    inline = ActionPermissionInline(queryset.model, modeladmin.admin_site)
    formsets = []
    for obj in queryset:
        prefixes = {}
        FormSet = inline.get_formset(request, obj)
        prefix = "%s-%s" % (FormSet.get_default_prefix(), obj.pk)
        prefixes[prefix] = prefixes.get(prefix, 0) + 1
        if prefixes[prefix] != 1:
            prefix = "%s-%s" % (prefix, prefixes[prefix])
        if request.POST.get('post'):
            formset = FormSet(data=request.POST, files=request.FILES,
                              instance=obj, prefix=prefix)
        else:
            formset = FormSet(instance=obj, prefix=prefix)
        formsets.append(formset)

    media = modeladmin.media
    inline_admin_formsets = []
    for formset in formsets:
        fieldsets = list(inline.get_fieldsets(request))
        inline_admin_formset = helpers.InlineAdminFormSet(inline, formset, fieldsets)
        inline_admin_formsets.append(inline_admin_formset)
        media = media + inline_admin_formset.media

    ordered_objects = opts.get_ordered_objects()
    if request.POST.get('post'):
        if all_valid(formsets):
            for formset in formsets:
                formset.save()
        else:
            modeladmin.message_user(request, '; '.join(
                err.as_text() for formset in formsets for err in formset.errors
            ))
        # redirect to full request path to make sure we keep filter
        return HttpResponseRedirect(request.get_full_path())

    context = {
        'errors': ActionErrorList(formsets),
        'title': ugettext('Permissions for %s') % force_text(opts.verbose_name_plural),
        'inline_admin_formsets': inline_admin_formsets,
        'app_label': app_label,
        'change': True,
        'ordered_objects': ordered_objects,
        'form_url': mark_safe(''),
        'opts': opts,
        'target_opts': queryset.model._meta,
        'content_type_id': ContentType.objects.get_for_model(queryset.model).id,
        'save_as': False,
        'save_on_top': False,
        'is_popup': False,
        'media': mark_safe(media),
        'show_delete': False,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
        'queryset': queryset,
        "object_name": force_text(opts.verbose_name),
    }
    template_name = getattr(modeladmin, 'permission_change_form_template', [
        "admin/%s/%s/permission_change_form.html" % (app_label, opts.object_name.lower()),
        "admin/%s/permission_change_form.html" % app_label,
        "admin/permission_change_form.html"
    ])
    return render_to_response(template_name, context,
                              context_instance=template.RequestContext(request))
edit_permissions.short_description = _("Edit permissions for selected %(verbose_name_plural)s")


class PermissionAdmin(admin.ModelAdmin):
    list_display = ('codename', 'content_type', 'user', 'group', 'approved')
    list_filter = ('approved', 'content_type')
    search_fields = ('user__username', 'group__name', 'codename')
    raw_id_fields = ('user', 'group', 'creator')
    generic_fields = ('content_object',)
    actions = ['approve_permissions']
    fieldsets = (
        (None, {'fields': ('codename', ('content_type', 'object_id'))}),
        (_('Permitted'), {'fields': ('approved', 'user', 'group')}),
        (_('Creation'), {'fields': ('creator', 'date_requested', 'date_approved')}),
    )

    def formfield_for_dbfield(self, db_field, **kwargs):
        # For generic foreign keys marked as generic_fields we use a special widget
        names = [f.fk_field
                 for f in self.model._meta.virtual_fields
                 if f.name in self.generic_fields]
        if db_field.name in names:
            for gfk in self.model._meta.virtual_fields:
                if gfk.fk_field == db_field.name:
                    kwargs['widget'] = GenericForeignKeyRawIdWidget(
                        gfk.ct_field, self.admin_site._registry.keys())
                    break
        return super(PermissionAdmin, self).formfield_for_dbfield(db_field, **kwargs)

    def queryset(self, request):
        user = request.user
        if (user.is_superuser or
                user.has_perm('permissions.change_foreign_permissions')):
            return super(PermissionAdmin, self).queryset(request)
        return super(PermissionAdmin, self).queryset(request).filter(creator=user)

    def approve_permissions(self, request, queryset):
        for permission in queryset:
            permission.approve(request.user)
        message = ungettext(
            "%(count)d permission successfully approved.",
            "%(count)d permissions successfully approved.", len(queryset))
        self.message_user(request, message % {'count': len(queryset)})
    approve_permissions.short_description = _("Approve selected permissions")

admin.site.register(Permission, PermissionAdmin)

if actions:
    admin.site.add_action(edit_permissions)
