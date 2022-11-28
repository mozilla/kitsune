from wagtail.contrib.modeladmin.options import ModelAdmin, modeladmin_register

from kitsune.wiki.models import Document


class WikiDocumentAdmin(ModelAdmin):
    model = Document
    menu_label = "Wiki Document"
    add_to_settings_menu = False
    exclude_from_explorer = False
    add_to_admin_menu = True
    menu_order = 200
    list_display = (
        "title",
        "locale",
        "parent",
        "products",
    )


modeladmin_register(WikiDocumentAdmin)
