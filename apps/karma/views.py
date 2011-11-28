import jingo

from access.decorators import login_required, permission_required


@login_required
@permission_required('karma.view_dashboard')
def questions_dashboard(request):
    """Karma dashboard for the support forum."""
    return jingo.render(request, 'karma/dashboards/questions.html')
