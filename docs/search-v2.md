# Search v2

## Testing on Staging

### Enabling in Instant Search

Open [support.allizom.org](https://support.allizom.org) and then open Firefox's [Web Console](https://developer.mozilla.org/en-US/docs/Tools/Web_Console).

Paste the following JS in, and hit return on your keyboard:

```
window.localStorage.setItem("enable_search_v2", "true")
```

Pasting JS into your Web Console without understanding what it does is a *very bad idea*,
so to explain this:

* `window.localStorage` uses the [Local Storage API](https://developer.mozilla.org/en-US/docs/Web/API/Window/localStorage) to get access to a small store which sites can use to store small pieces of information in your browser.
* `setItem()` is the function which allows us to write a piece of information to the store.
* `"enable_search_v2"` is the name of the piece of information we're storing.
* `"true"` is its value.

Now refresh the page and instant search should be using search v2.
You can check this by using some of the syntax which search v2 supports,
like wildcards.
A search for `fir*` in search v1 should return next to no results,
whereas in search v2 it should return at least as many as a search for `firefox`.

### Disabling in Instant Search

You can disable search v2 in instant search by opening Firefox's Web Console on support.allizom.org again,
but running this snippet instead:

```
window.localStorage.removeItem("enable_search_v2")
```

* `window.localStorage` is the same Local Storage API from before.
* `removeItem()` is the function to remove a piece of information.
* `"enable_search_v2"` is the name of the piece of information to remove.

Refresh the page,
and instant search will be using search v1 again.

## Development tips

### Adding fields to a live index

Elastic supports adding new fields to an existing mapping,
along with some other operations:
https://www.elastic.co/guide/en/elasticsearch/reference/7.9/mapping.html#add-field-mapping

To know whether a change you make to a Document will work in prod,
try it locally having already set up the mapping:

```
./manage.py es7_init --limit TestDocument

... make changes to TestDocument ...

./manage.py es7_init --limit TestDocument
```

If that fails with an error,
you'll need to create a new index with the new mapping,
and reindex everything into that index.

However if it succeeds then it should also work on prod.

Once the changes are deployed to prod,
and the mapping is updated with `es7_init`,
some documents may need to be reindexed.
This is because we disable dynamic mapping in `SumoDocument`,
to prevent a dynamic mapping of the wrong type being set up before `es7_init` was able to be run during a deployment.

So to ensure no data is missing from the index,
run something like:

```
./manage.py es7_reindex --limit TestDocument --updated-after <datetime of deploy> --updated-before <datetime of mapping update>
```

### Indexing performance

When adding or editing elastic documents,
you might want to add the `--print-sql-count` argument when testing out your changes,
to see how many SQL queries are being executed:

```sh
CELERY_TASK_ALWAYS_EAGER=True ./manage.py es7_reindex --print-sql-count --bulk-count=100 --count=100
```

If the result is much less than 100,
then you have a well optimized document for indexing.
However, if the result is some multiple of 100,
then unfortunately one or more SQL queries are being executed for each instance being indexed.
Consider using some combination of
[`select_related`](https://docs.djangoproject.com/en/dev/ref/models/querysets/#select-related),
[`prefetch_related`](https://docs.djangoproject.com/en/dev/ref/models/querysets/#prefetch-related)
or [annotations](https://docs.djangoproject.com/en/dev/ref/models/querysets/#annotate)
to bring that number down.

### Datetimes and timezones

As a first step in our migration to using timezone-aware datetimes throughout the application,
all datetimes stored in Elastic should be timezone-aware,
so as to avoid having to migrate them later.

If inheriting from `SumoDocument`,
any naive datetime set in a `Date` field will be automatically converted into a timezone-aware datetime,
with the naive datetime assumed to be in the application's `TIME_ZONE`.

To avoid loss of precision around DST switches,
where possible aware datetimes should be set.
To generate an aware datetime do:

```python
import datetime, timezone

datetime.now(timezone.utc)
```

This should be used instead of
[`django.utils.timezone.now()`](https://docs.djangoproject.com/en/2.2/ref/utils/#django.utils.timezone.now)
as that returns a naive or aware datetime depending on the value of `USE_TZ`, whereas we want datetimes in Elastic to always be timezone-aware.

### Print ElasticSearch queries in your development console

You can set the following variable in your .env file to enable the logging of the queries that are sent to your local ElasticSearch instance.

```
ES7_ENABLE_LOGGING=True
```