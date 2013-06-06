from jingo import register, env
import jinja2

from kitsune.dashboards.personal import personal_dashboards


@register.function
@jinja2.contextfunction
def personal_dashboard_tabs(context, active_tab):
    """Render the tabs for the user/group dashboard."""
    c = {'dashboards': personal_dashboards(context['request']),
         'user': context['request'].user,
         'active_tab': active_tab,
         'request': context['request']}
    t = env.get_template('dashboards/includes/personal_tabs.html').render(c)
    return jinja2.Markup(t)
