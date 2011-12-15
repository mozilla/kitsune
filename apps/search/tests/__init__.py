from django.test.client import RequestFactory

# Dummy request for passing to question_searcher() and brethren.
# There's no reason to use test_utils' RequestFactory.
dummy_request = RequestFactory().get('/')
