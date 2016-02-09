from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin.widgets import ForeignKeyRawIdWidget


generic_script = """
<script type="text/javascript">
function showGenericRelatedObjectLookupPopup(ct_select, triggering_link, url_base) {
    var url = content_types[ct_select.options[ct_select.selectedIndex].value];
    if (url != undefined) {
        triggering_link.href = url_base + url;
        return showRelatedObjectLookupPopup(triggering_link);
    }
    return false;
}
</script>
"""


class GenericForeignKeyRawIdWidget(ForeignKeyRawIdWidget):
    def __init__(self, ct_field, cts=[], attrs=None):
        self.ct_field = ct_field
        self.cts = cts
        forms.TextInput.__init__(self, attrs)

    def render(self, name, value, attrs=None):
        if attrs is None:
            attrs = {}
        related_url = '../../../'
        params = self.url_parameters()
        if params:
            url = '?' + '&amp;'.join(['%s=%s' % (k, v) for k, v in params.iteritems()])
        else:
            url = ''
        if 'class' not in attrs:
            attrs['class'] = 'vForeignKeyRawIdAdminField'
        output = [forms.TextInput.render(self, name, value, attrs)]
        output.append(
            """%(generic_script)s
                <a href="%(related)s%(url)s"
                    class="related-lookup"
                    id="lookup_id_%(name)s"
                    onclick="return showGenericRelatedObjectLookupPopup(
                        document.getElementById('id_%(ct_field)s'), this, '%(related)s%(url)s');">
            """ % {
                'generic_script': generic_script,
                'related': related_url,
                'url': url,
                'name': name,
                'ct_field': self.ct_field
            })
        output.append(
            '<img src="%s/admin/img/selector-search.gif" width="16" height="16" alt="%s" /></a>'
            % (settings.STATIC_URL, _('Lookup')))

        from django.contrib.contenttypes.models import ContentType
        content_types = """
        <script type="text/javascript">
        var content_types = new Array();
        %s
        </script>
        """ % ('\n'.join([
            "content_types[%s] = '%s/%s/';" % (
                ContentType.objects.get_for_model(ct).id,
                ct._meta.app_label,
                ct._meta.object_name.lower()
            ) for ct in self.cts]))
        return mark_safe(u''.join(output) + content_types)

    def url_parameters(self):
        return {}
