from jingo import register, env
import jinja2

from dashboards.personal import personal_dashboards


@register.function
@jinja2.contextfunction
def personal_dashboard_tabs(context, active_signature):
    """Render the tabs for the user/group dashboard."""
    c = {'dashboards': personal_dashboards(context['request']),
         'dashboard_signature': active_signature}
    t = env.get_template('dashboards/includes/personal_tabs.html').render(**c)
    return jinja2.Markup(t)
