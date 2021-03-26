from functools import wraps

from django.contrib.auth.models import User
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect

from kitsune.sumo.urlresolvers import reverse
from kitsune.users.models import Profile


def get_profile_from_url(func):
    @wraps(func)
    def wrapped_func(request, *args, **kwargs):
        # The browser replaces '+' in URL's with ' ' but since we never have ' ' in
        # URL's we can assume everytime we see ' ' it was a '+' that was replaced.
        # We do this to deal with legacy usernames that have a '+' in them.

        username = kwargs.pop("username")
        username = username.replace(" ", "+")

        user = User.objects.filter(username=username).first()

        if not user:
            try:
                user = get_object_or_404(User, id=username)
            except ValueError:
                raise Http404("No Profile matches the given query.")
            return redirect(reverse("users.profile", args=(user.username,)))

        user_profile = get_object_or_404(Profile, user__id=user.id)

        if not (request.user.has_perm("users.deactivate_users") or user_profile.user.is_active):
            raise Http404("No Profile matches the given query.")

        kwargs["user_profile"] = user_profile
        return func(request, *args, **kwargs)

    return wrapped_func
