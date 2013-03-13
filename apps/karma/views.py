from django.shortcuts import render

from access.decorators import login_required, permission_required


@login_required
@permission_required('karma.view_dashboard')
def questions_dashboard(request):
    """Karma dashboard for the support forum."""
    return render(request, 'karma/dashboards/questions.html')
