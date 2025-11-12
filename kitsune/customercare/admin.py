from django import forms
from django.contrib import admin
from django.utils.html import format_html

from kitsune.customercare.models import SupportTicket
from kitsune.sumo.utils import PrettyJSONEncoder


class SupportTicketForm(forms.ModelForm):
    zendesk_tags = forms.JSONField(
        initial=list,
        required=False,
        encoder=PrettyJSONEncoder,
    )

    class Meta:
        model = SupportTicket
        fields = "__all__"


class SupportTicketAdmin(admin.ModelAdmin):
    form = SupportTicketForm
    list_display = (
        "id",
        "subject",
        "email",
        "product",
        "status_badge",
        "zendesk_ticket_id",
        "created",
    )
    list_display_links = ("id", "subject")
    list_filter = ("status", "product", "created")
    search_fields = ("subject", "description", "email", "zendesk_ticket_id")
    readonly_fields = ("created", "zendesk_ticket_id")
    date_hierarchy = "created"
    ordering = ("-created",)
    raw_id_fields = ("user",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("product", "user")

    @admin.display(description="Status")
    def status_badge(self, obj):
        colors = {
            SupportTicket.STATUS_PENDING: "#f0ad4e",
            SupportTicket.STATUS_SENT: "#5cb85c",
            SupportTicket.STATUS_FLAGGED: "#d9534f",
            SupportTicket.STATUS_REJECTED: "#777",
        }
        color = colors.get(obj.status, "#777")
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display(),
        )


admin.site.register(SupportTicket, SupportTicketAdmin)
