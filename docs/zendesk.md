# Zendesk integration

## Using `requests` to query the API

During development being able to query the API manually to fetch details about field IDs,
user statuses,
and so on is very useful.

To do so use a snippet of code like the following in `./manage.py shell_plus`:

```python
import requests
base = f"https://{settings.ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/"
auth = requests.auth.HTTPBasicAuth(settings.ZENDESK_USER_EMAIL+"/token", settings.ZENDESK_API_TOKEN)

requests.get(base+"foobar", auth=auth).json()

requests.post(base+"barfoo", auth=auth, json={}).json()
```
