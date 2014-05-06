from django.shortcuts import render

def home(request):

    data = {}

    return render(request, 'community/index.html', data)


def contributor_results(request):

    data = {}

    return render(request, 'community/contributor_results.html', data)


def view_all(request):

    data = {}

    return render(request, 'community/view_all.html', data)
