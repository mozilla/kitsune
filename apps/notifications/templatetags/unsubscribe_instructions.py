from django import template


register = template.Library()


@register.inclusion_tag('notifications/email/unsubscribe.ltxt')
def unsubscribe_instructions(watch):
    """Return instructions and link for unsubscribing from the given watch."""
    return {'watch': watch}
