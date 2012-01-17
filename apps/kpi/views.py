import jingo

from access.decorators import login_required, permission_required


@login_required
@permission_required('users.view_kpi_dashboard')
def dashboard(request):
    return jingo.render(request, 'kpi/dashboard.html')
