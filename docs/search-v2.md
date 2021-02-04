# Search v2

## Testing

### Enabling in Instant Search

Open [support.mozilla.org](https://support.mozilla.org) and then open Firefox's [Web Console](https://developer.mozilla.org/en-US/docs/Tools/Web_Console).

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

You can disable search v2 in instant search by opening Firefox's Web Console on support.mozilla.org again,
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
CELERY_TASK_ALWAYS_EAGER=True ./manage.py es7_reindex --print-sql-count --sql-chunk-size=100 --count=100
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
ES7_ENABLE_CONSOLE_LOGGING=True
```

### Simulate slow and out of order query responses

To test how Instant Search behaves with slow and out of order responses you can add a snippet like this:

```
from time import sleep
from random import randint
sleep(randint(1, 10))
```

to `kitsune.search.v2.views.simple_search`.

### Synonyms

The `elasticsearch/dictionaries/synonyms` path contains a text file for each of our search-enabled locales,
where synonyms are in the
[Solr format](https://www.elastic.co/guide/en/elasticsearch/reference/7.10/analysis-synonym-graph-tokenfilter.html#_solr_synonyms_2).

`expand` defaults to `True`,
so synonyms with no explicit mapping resolve to all elements in the list.
That is to say:

```
start, open, run
```

is equivalent to:

```
start, open, run => start, open, run
```

It's also worth noting that these synonyms are applied at *query* time,
not index time.

That is to say,
if a document contained the phrase:

> Firefox won't play music.

and we had a synonym set up as:

```
music => music, audio
```

Then the search query:

> firefox won't play audio

would **not** match that document.

#### Hyponyms and hypernyms (subtypes and supertypes)

The synonym files can also be used to define relations between
[hyponyms and hypernyms (subtypes and supertypes)](https://en.wikipedia.org/wiki/Hyponymy_and_hypernymy).

For example,
a user searching for or posting about a problem with Facebook could use the phrase "Facebook isn't working",
or "social media isn't working".
Another user searching for or posting about a problem with Twitter could use the phrase "Twitter isn't working",
or "social media isn't working".

A simple synonym definition like:

```
social, facebook, face book, twitter
```

isn't sufficient here,
as a user querying about a problem with Facebook clearly doesn't have one with Twitter.

Similarly a rule like:

```
social => social, facebook, face book, twitter
```

only captures the case where a user has posted about Facebook not working and searched for social media not working,
not the reverse.

So in this case a set of synonyms should be defined,
like so:

```
social, facebook, face book
social, twitter
```

With the hypernyms (supertypes) defined across all lines,
and the hyponyms (subtypes) defined on one line.

This way,
a search for "social" would also become one for "facebook", "face book" and "twitter".
Whereas a search for "twitter" would also become one for "social",
but *not* "facebook" or "face book".


#### Interaction with the rest of the analysis chain

All the analyzers which we apply to a document are also applied to the synonyms,
such as tokenizers, stemmers and stop word filters.

This means it's not necessary to specify the plural or conjugated forms of words,
as post-analysis they *should* end up as the same token.

Hyphen-separated and space separated words will analyze to the same set of tokens.

For instance in en-US,
all these synonyms would do nothing at all:

```
de activate, de-activate
load, loading, loaded
bug, bugs
```

##### Stop words

Synonyms containing stop words (such as "in" or "on") must be treated with care,
as the stop words will also be filtered out of the synonyms.

For example,
these two rules produce the same result in the en-US analysis chain:

```
addon, add on
addon, add
```

So a [character mapping](#character-mappings) should be used to turn phrases containing those stop words into ones which don't.
Those resulting phrases can then be used in the synonyms definition.

#### Applying to all locales

There's also an `_all.txt` file,
which specifies synonyms which should be applied across *all* locales.
Suitable synonyms here include brand names or specific technical terms which won't tend to be localized.

#### Updating

In development synonyms can be updated very easily.
Save your changes in the text file and run:

```
./manage.py es7_init --reload-search-analyzers
```

If no other changes were made to the index configurations,
then this should apply successfully,
and your already-indexed data will persist within the index and not require any indexing
(because these synonyms are applied at query time).

##### On production

The synonym files need to be put in a bundle and uploaded to the Elastic Cloud.

`cd` into the `elasticsearch` directory,
and run the `create_bundle.sh` script to create a zip file with the appropriate directory structure.
(You'll need to have `zip` installed for this command to work.)

Then,
either [create](https://www.elastic.co/guide/en/cloud/current/ec-custom-bundles.html#ec-add-your-plugin) an extension,
or [update](https://www.elastic.co/guide/en/cloud/current/ec-custom-bundles.html#ec-update-bundles-and-plugins) the previously created extension.

And in either case,
[update the deployment configuration](https://www.elastic.co/guide/en/cloud/current/ec-custom-bundles.html#ec-update-bundles)
with the custom extension.

```eval_rst
.. Note::
  When updating the deployment after updating an already-existing extension,
  Elastic Cloud may say that no changes are being applied.
  That isn't true,
  and through testing it seems like the extension is being updated,
  and the search analyzers are being reloaded automatically.

  From testing,
  this seems to be the only approach to update and reload synonyms on the Elastic Cloud.
  Updating the extension,
  restarting the cluster and using the reload-search-analyzers command *won't* work.

  Thankfully there's an open issue upstream to make managing synonyms easier with an API:
  https://github.com/elastic/elasticsearch/issues/38523
```

### Character mappings

Character mappings *cannot* be dynamically updated,
this is because they're applied at index time.
So any changes to a character mapping requires a re-index.

Taking the addon example from above,
we'd want to create character mappings like:

```
[
  "add on => addon",
  "add-on => addon",
]
```

Post-tokenization `addon` doesn't contain an `on` token,
so this is a suitable phrase to replace with.

Unlike synonyms,
character mappings are applied before any other part of the analysis chain,
so space separated and hyphen-separated phrases need to both be added.

In theory plural and conjugated forms of words also need to be specified,
however in practice plural words tend to be covered by the singular replacement as well
(e.g. "add on" is a substring in "add ons",
so "add ons" is replaced by "addons")
and there is marginal benefit to defining *every single* conjugation of a verb.
