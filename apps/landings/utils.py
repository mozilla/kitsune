import waffle


def show_ia(request):
	"""Return True if the new IA should be shown to the user."""
	# Only show the IA to en-US users that are not on mobile and have
	# the waffle flag active.
	if (request.locale == 'en-US' and
		not request.MOBILE and
		waffle.flag_is_active(request, 'ia-enabled')):
		return True
