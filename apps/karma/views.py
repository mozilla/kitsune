import jingo


def questions_dashboard(request):
    """Karma dashboard for the support forum."""
    return jingo.render(request, 'karma/dashboards/questions.html')
