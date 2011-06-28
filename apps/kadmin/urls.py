from django.contrib import admin
from django.shortcuts import redirect

from sumo.urlresolvers import reverse


# Hijack the admin login page.
def login(request):
    url = '%s?next=%s' % (reverse('users.login'), request.path)
    return redirect(url)

admin.site.login = login
