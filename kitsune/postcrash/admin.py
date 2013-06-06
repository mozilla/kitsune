from django.contrib import admin

from kitsune.postcrash.models import Signature


class SignatureAdmin(admin.ModelAdmin):
    list_display = ['__unicode__', 'signature', 'document']
    list_editable = ['signature', 'document']
    raw_id_fields = ['document']

admin.site.register(Signature, SignatureAdmin)
