from jingo import register, env
import jinja2

from dashboards.personal import personal_dashboards


@register.function
@jinja2.contextfunction
def user_dashboard_tabs(context, active_tab_slug):
    """Render the tabs for the user/group dashboard."""
    c = {'dashboards': personal_dashboards(context['request']),
         'active': active_tab_slug}
    t = env.get_template('dashboards/includes/user_tabs.html').render(**c)
    return jinja2.Markup(t)
