import jingo


def dashboard(request):
    return jingo.render(request, 'kpi/dashboard.html')
