# Search


## Development tips

### Adding fields to a live index

Elastic supports adding new fields to an existing mapping,
along with some other operations:
https://www.elastic.co/guide/en/elasticsearch/reference/current/mapping.html#add-field-mapping

To know whether a change you make to a Document will work in prod,
try it locally having already set up the mapping:

```
./manage.py es_init --limit TestDocument

... make changes to TestDocument ...

./manage.py es_init --limit TestDocument
```

If that fails with an error,
you'll need to create a new index with the new mapping,
and reindex everything into that index.

However if it succeeds then it should also work on prod.

Once the changes are deployed to prod,
and the mapping is updated with `es_init`,
some documents may need to be reindexed.
This is because we disable dynamic mapping in `SumoDocument`,
to prevent a dynamic mapping of the wrong type being set up before `es_init` was able to be run during a deployment.

So to ensure no data is missing from the index,
run something like:

```
./manage.py es_reindex --limit TestDocument --updated-after "2024-01-01 10:00:00" --updated-before "2024-01-01 12:00:00"
```

### Indexing performance

When adding or editing elastic documents,
you might want to add the `--print-sql-count` argument when testing out your changes,
to see how many SQL queries are being executed:

```sh
CELERY_TASK_ALWAYS_EAGER=True ./manage.py es_reindex --print-sql-count --sql-chunk-size 100 --count 100
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

## Search Management Commands

Kitsune provides two key management commands for working with Elasticsearch indices: `es_init` and `es_reindex`. These commands handle index initialization, migration, and document reindexing.

### es_init Command

The `es_init` command initializes Elasticsearch document types and manages index aliases. It's used to create new indices, update mappings, and handle index migrations.

#### Basic Usage

```bash
# Initialize all document types (creates indices and aliases on first run)
./manage.py es_init

# Initialize specific document types only
./manage.py es_init --limit WikiDocument QuestionDocument

# Reload search analyzers (useful after updating synonyms)
./manage.py es_init --reload-search-analyzers
```

#### Migration Options

The command supports two types of migrations:

**Write Migration (`--migrate-writes`)**
- Creates a new index with a timestamp suffix
- Points the `_write` alias to the new index
- Used when you need to create a completely new index with updated mappings

```bash
./manage.py es_init --migrate-writes
```

**Read Migration (`--migrate-reads`)**
- Updates the `_read` alias to point where the `_write` alias points
- Used to switch read operations to the new index after write migration is complete

```bash
./manage.py es_init --migrate-reads
```

**Combined Migration (Zero-Downtime Deployment)**
```bash
# Step 1: Create new index and migrate writes
./manage.py es_init --migrate-writes

# Step 2: Reindex data to new index (see es_reindex section)
./manage.py es_reindex

# Step 3: Switch reads to new index
./manage.py es_init --migrate-reads
```

#### How It Works

- If no write alias exists (first run), the command automatically creates both indices and aliases
- If indices exist, it updates the existing index mapping (when possible)
- Uses timestamped index names (e.g., `wikidocument_20241201_120000`) with aliases for read/write operations
- Handles mapping conflicts by requiring explicit migration steps

### es_reindex Command

The `es_reindex` command populates Elasticsearch indices with data from the database. It supports incremental updates, performance optimization, and selective reindexing.

#### Basic Usage

```bash
# Reindex all document types
./manage.py es_reindex

# Reindex specific document types
./manage.py es_reindex --limit WikiDocument QuestionDocument

# Reindex a percentage of documents (useful for testing)
./manage.py es_reindex --percentage 10

# Reindex a specific number of documents
./manage.py es_reindex --count 1000
```

#### Time-Based Filtering

```bash
# Reindex documents updated after a specific date
./manage.py es_reindex --updated-after "2024-01-01"

# Reindex documents updated before a specific date
./manage.py es_reindex --updated-before "2024-01-01 12:00:00"

# Reindex documents updated within a date range
./manage.py es_reindex --updated-after "2024-01-01" --updated-before "2024-01-02"
```

#### Performance Tuning

```bash
# Adjust chunk sizes for performance
./manage.py es_reindex --sql-chunk-size 500 --elastic-chunk-size 100

# Set custom timeout for bulk operations
./manage.py es_reindex --timeout 60

# Monitor SQL query performance
./manage.py es_reindex --print-sql-count --count 100
```

#### Production Reindexing

For production environments, use `CELERY_TASK_ALWAYS_EAGER=True` to process tasks synchronously:

```bash
# Reindex all document types in production
CELERY_TASK_ALWAYS_EAGER=True ./manage.py es_reindex --limit WikiDocument
CELERY_TASK_ALWAYS_EAGER=True ./manage.py es_reindex --limit QuestionDocument
CELERY_TASK_ALWAYS_EAGER=True ./manage.py es_reindex --limit AnswerDocument
CELERY_TASK_ALWAYS_EAGER=True ./manage.py es_reindex --limit ProfileDocument
CELERY_TASK_ALWAYS_EAGER=True ./manage.py es_reindex --limit ForumDocument
```

#### How It Works

- Queries the database for objects to index using Django ORM
- Processes documents in configurable chunks to avoid memory issues
- Sends bulk requests to Elasticsearch for efficient indexing
- Uses Celery tasks for background processing (unless `CELERY_TASK_ALWAYS_EAGER=True`)
- Supports both full reindexing and incremental updates based on modification dates

### Common Workflows

#### Creating New Indices

When you need to create completely new indices (e.g., for mapping changes that require reindexing):

```bash
# 1. Create new index and switch writes
./manage.py es_init --migrate-writes

# 2. Populate the new index
./manage.py es_reindex

# 3. Switch reads to new index (zero downtime)
./manage.py es_init --migrate-reads
```

#### Updating Existing Indices

For compatible mapping changes that don't require full reindexing:

```bash
# Update mapping on existing index
./manage.py es_init

# Optionally reindex recently updated documents
./manage.py es_reindex --updated-after "2024-01-01"
```

#### Synonym Updates

When updating search synonyms (no data reindexing required):

```bash
# Reload search analyzers to pick up synonym changes
./manage.py es_init --reload-search-analyzers
```

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
ES_ENABLE_CONSOLE_LOGGING=True
```

### Simulate slow and out of order query responses

To test how Instant Search behaves with slow and out of order responses you can add a snippet like this:

```
from time import sleep
from random import randint
sleep(randint(1, 10))
```

to `kitsune.search.views.simple_search`.

### Synonyms

The `kitsune/search/dictionaries/synonyms` path contains a text file for each of our search-enabled locales,
where synonyms are in the
[Solr format](https://www.elastic.co/guide/en/elasticsearch/reference/current/analysis-synonym-graph-tokenfilter.html#_solr_synonyms_2).

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

It's also worth noting that these synonyms are applied at _query_ time,
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
but _not_ "facebook" or "face book".

#### Interaction with the rest of the analysis chain

All the analyzers above the synonym token filter in the analyzer chain are also applied to the synonyms,
such as our tokenizers, stemmers and stop word filters.

This means it's not necessary to specify the plural or conjugated forms of words,
as post-analysis they _should_ end up as the same token.

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
which specifies synonyms which should be applied across _all_ locales.
Suitable synonyms here include brand names or specific technical terms which won't tend to be localized.

#### Updating

In development synonyms can be updated very easily.
Save your changes in the text file and run:

```
./manage.py es_init --reload-search-analyzers
```

If no other changes were made to the index configurations,
then this should apply successfully,
and your already-indexed data will persist within the index and not require any indexing
(because these synonyms are applied at query time).

##### On production

The synonym files need to be put in a bundle and uploaded to the Elastic Cloud.

Run the `bin/create_elastic_bundle.sh` script to create a zip file with the appropriate directory structure.
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

Character mappings _cannot_ be dynamically updated,
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
and there is marginal benefit to defining _every single_ conjugation of a verb.

## Production Deployment

This section describes the process for creating a new upgraded Elasticsearch deployment without downtime. This workflow is essential for major version upgrades or when significant infrastructure changes are required.

### Overview

The production deployment process follows a zero-downtime approach by:

1. Setting up a new Elasticsearch deployment alongside the existing one
2. Creating specialized application pods for index management
3. Populating the new deployment with data
4. Switching traffic to the new deployment
5. Decommissioning the old deployment

### Step 1: Set Up New Elasticsearch Deployment

Create a new production deployment in Elastic Cloud:

1. **Create Deployment**
   - Go to [https://cloud.elastic.co/deployments](https://cloud.elastic.co/deployments)
   - Choose "Create hosted deployment" button
   - Select "Elasticsearch" option on left
   - Ensure you choose "us-west1" for region
   - Choose "Vector Search Optimized" for hardware profile
   - Click "Create hosted deployment" in bottom right corner
   - Save the new authentication credentials provided

2. **Deployment Naming Convention**
   - Use consistent naming: `sumo-nonprod-stage-v9`, `sumo-nonprod-dev-v9`, `sumo-prod-prod-v9`
   - Include version number for tracking major upgrades

### Step 2: Add Synonyms and Extensions

Configure the new deployment with required extensions:

1. **Access Deployment Settings**
   - From [https://cloud.elastic.co/deployments/](https://cloud.elastic.co/deployments/), select your new deployment
   - Under "Actions" in top right corner, select "Edit deployment"
   - Click "Manage user settings and extensions" link

2. **Add Extensions**
   - In the flyout, select "Extensions"
   - Add synonyms bundle
   - Add analysis-stempel plugin
   - Click back, then click Save (you must click save!)

### Step 3: Create Specialized Application Pod

Set up a temporary application pod for index management:

1. **Enable ES9 Admin Pod**
   - Add to appropriate values file in webservices-infra repo:
   ```yaml
   enableES9Admin: true
   ```

2. **Configure Secrets**
   - For stage: Go to [stage-gke-app-secrets-temp-es9](https://console.cloud.google.com/security/secret-manager/secret/stage-gke-app-secrets-temp-es9?project=moz-fx-sumo-nonprod)
   - For prod: Switch to sumo-prod project, then access [prod-gke-app-secrets-temp-es9](https://console.cloud.google.com/security/secret-manager/secret/prod-gke-app-secrets-temp-es9?project=moz-fx-sumo-prod)
   - Update secrets with:
     - `ES_CLOUD_ID`: From your new ES deployment
     - `ES_HTTP_AUTH`: Authentication from your new ES deployment
   - Submit changes as PR for webservices-infra

### Step 4: Initialize and Populate Indices

Use the specialized pod to set up the new deployment:

1. **Verify Configuration**
   ```bash
   # Get shell access to the new indexing pod
   ./manage.py shell_plus
   
   # Verify correct deployment is configured
   from kitsune.settings import ES_CLOUD_ID
   print(ES_CLOUD_ID)
   exit
   ```

2. **Create Indices**
   ```bash
   # Initialize all document types
   ./manage.py es_init
   ```

3. **Verify Index Creation**
   - Go to Kibana for your deployment
   - Under "Content" in left navigation, click "Index Management"
   - Confirm four indices exist with date stamps (e.g., `wikidocument_20241201_120000`)
   - *NOTE*:: We currently have four indexes but five types of documents. This is becase AnswerDocument and QuestionDocument share the same index. So if you ever re-index per document type, don't forget AnswerDocument - it is easy to overlook as it does not have an index named after it.

4. **Populate Indices**
   ```bash
   # Reindex all document types
   CELERY_TASK_ALWAYS_EAGER=True ./manage.py es_reindex --limit WikiDocument
   CELERY_TASK_ALWAYS_EAGER=True ./manage.py es_reindex --limit QuestionDocument
   CELERY_TASK_ALWAYS_EAGER=True ./manage.py es_reindex --limit AnswerDocument
   CELERY_TASK_ALWAYS_EAGER=True ./manage.py es_reindex --limit ProfileDocument
   CELERY_TASK_ALWAYS_EAGER=True ./manage.py es_reindex --limit ForumDocument
   ```

5. **Handle Resource Constraints (if needed)**
   If you encounter OOM errors or pod bouncing, use smaller chunk sizes:
   ```bash
   CELERY_TASK_ALWAYS_EAGER=True ./manage.py es_reindex --limit WikiDocument --sql-chunk-size 100 --elastic-chunk-size 50
   CELERY_TASK_ALWAYS_EAGER=True ./manage.py es_reindex --limit QuestionDocument --sql-chunk-size 100 --elastic-chunk-size 50
   CELERY_TASK_ALWAYS_EAGER=True ./manage.py es_reindex --limit AnswerDocument --sql-chunk-size 100 --elastic-chunk-size 50
   CELERY_TASK_ALWAYS_EAGER=True ./manage.py es_reindex --limit ProfileDocument --sql-chunk-size 100 --elastic-chunk-size 50
   CELERY_TASK_ALWAYS_EAGER=True ./manage.py es_reindex --limit ForumDocument --sql-chunk-size 100 --elastic-chunk-size 50
   ```

### Step 5: Deploy to Production

Switch the main application to use the new deployment:

1. **Update Production Secrets**
   - Update [prod-gke-app-secrets](https://console.cloud.google.com/security/secret-manager/secret/prod-gke-app-secrets?project=moz-fx-sumo-prod)
   - Set `ES_CLOUD_ID` and `ES_HTTP_AUTH` to values from new deployment

2. **Deploy Release**
   - Create release via normal release process
   - This switches all production traffic to the new Elasticsearch deployment

3. **Sync Recent Changes**
   - Run incremental reindex to catch any data changes during deployment:
   ```bash
   # Sync data that changed during the deployment process
   ./manage.py es_reindex --updated-after "2024-01-01 10:00:00"
   ```

4. **Review and Testing**
   - Verify search functionality works correctly
   - Monitor application logs for Elasticsearch errors
   - Check performance metrics

### Step 6: Post-Deployment Cleanup

After confirming the new deployment is stable:

1. **Decommission Old Deployment**
   - Delete the old Elasticsearch deployment from Elastic Cloud
   - This frees up resources and reduces costs

2. **Clean Up Temporary Resources**
   - Remove ES9-related K8s resources (deployments, services, external secrets)
   - Delete temporary GCP secrets (`*-temp-es9`)
   - Remove `enableES9Admin: true` from values files

3. **Update Documentation**
   - Record the new deployment details for future reference
   - Update any monitoring or alerting configurations

### Important Notes

- **Zero Downtime**: This process ensures continuous service availability by running both deployments in parallel during the migration
- **Data Consistency**: The sync step catches any changes that occurred during the deployment window
- **Rollback Plan**: Keep the old deployment running until the new one is fully validated
- **Monitoring**: Watch both deployments during the transition period for any issues
- **Resource Planning**: Ensure sufficient resources are available to run both deployments simultaneously

This deployment process provides a safe, repeatable method for major Elasticsearch upgrades while maintaining service availability throughout the migration.
