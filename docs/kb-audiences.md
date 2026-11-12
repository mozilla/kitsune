# Knowledge bases

Staff define knowledge bases (KBs) on top of the one SUMO wiki. Every article belongs to at
least one. A public KB is readable by everyone; a private one only by the members of its
groups, which include enterprise company departments. Readers of a private KB search it with
the same hybrid search as everyone else, get a KB page and a menu entry, and see screenshots
nobody else can load. Reviewers can approve a revision to go live at a set time. Articles,
URLs, revisions and translations stay shared: a KB is a readership boundary, not a copy of the
wiki.

In code and in Django admin a KB is the `Audience` model (`kitsune/wiki/models.py`); the UI
says "knowledge base". Code: access in `kitsune/wiki/managers.py`, KB pages in
`kitsune/wiki/kb_views.py`, scheduled release in `kitsune/wiki/review.py`, private images in
`kitsune/gallery` (`storage.py`), KB search in `kitsune/search/hybrid.py`. How private
articles are indexed and filtered in retrieval is
[ADR 0006](architecture/decisions/0006-access-controlled-retrieval.md).

## Model

```
Audience (KB: is_public, is_listed) ──< groups (Django Group, optional)
   ▲                         ▲
   │ M2M through             │ FK, one KB per image
   │ DocumentAudience        │
Document (original)        Image
   └──< translations (inherit the original's KBs; never get rows)
```

- **Default KB**: slug `default` (`DEFAULT_AUDIENCE_SLUG`). Always public (a database check
  constraint), can't be deleted. New articles start in it, and images uploaded as public
  live in it. It has no KB page.
- **Named KBs**: public or private (`is_public`, private by default). A public KB can't have
  groups. A private KB without groups is readable by Staff and superusers only.
- **Listing** (`is_listed`) is opt-in: only a listed KB gets a page and a place in the menu,
  the directory and the search filter. An unlisted KB is a plain access list. Migrating from
  `restrict_to_groups` created one unlisted private KB per restricting group, named after the
  group.
- An article can be in several KBs; any one of them grants access.
- An assigned KB can't be deleted (`PROTECT` on `DocumentAudience` and `Image.audience`).

## Who can read an article

A viewer can read an article when any of these holds:

1. the viewer is a superuser or in the Staff group;
2. the original is in any public KB;
3. the original is in a private KB with a group among the viewer's **effective groups**:
   their direct groups, plus the company group of each enterprise company they belong to,
   directly or through a department (see [Enterprise support](enterprise-support.md)).

On top of that, the existing rule still hides articles without approved content from
everyone but their creators, reviewers in the locale, and Staff.

- **Fail-closed**: an original with no KB is readable by Staff and superusers only. Deleting
  a Django group removes its grant, which only narrows access.
- Access follows group membership, not contract status: leaving a company's groups ends it.
- Making a private article public exposes its whole history.

```
default (public)          "Clear the cache"
Contributors (public)     "Style guide"
Agents (private)          "Refund policy"          groups: Support agents
Northwind (private)       "Northwind SSO setup",   groups: Northwind (company)
                          "Refund policy"

Anonymous                  Clear the cache, Style guide
Support agent              + Refund policy
Northwind department member + Northwind SSO setup, Refund policy
Globex member              Clear the cache, Style guide
Staff                      everything
```

Check access with `Document.objects.visible(user)`, `get_visible()`,
`Document.is_visible_for(user)`, or `audience_access(effective_group_ids(user), prefix)` for
models that point at a document. `is_restricted` means "not in any public KB".

## Rules every code path must keep

- **Private looks missing.** Anything private a viewer can't read answers the same 404 as
  something that doesn't exist, never a 403. No surface (menu, directory, search filter,
  result tags, totals, page titles, error messages) reveals another KB's name, titles or
  counts.
- **Rendered HTML is one copy per article**, so it only embeds what every reader of the
  article can read. An include is allowed when the included article is public, or when the
  including article's private KBs are a subset of the included one's.
- **Changing access follows up on everything derived from it.** Assigning KBs or flipping a
  KB's visibility re-renders the families, clears their cached anonymous pages
  (`doc_page_cache`), refreshes retrieval, and gives redirect stubs their target's KBs.
- **Private pages load no analytics and stay out of shared caches.** Views that show private
  content set `suppress_analytics` in the context and pass the response through
  `mark_private()` (`Cache-Control: private, no-store`, `Referrer-Policy: strict-origin`).
  Search pages do this for every viewer with private access (`has_private_kb_access`).
- **Private URLs stay inside SUMO.** `add_short_links` skips private originals, so they never
  reach Bitly.
- **Groups through the visibility layer.** Never read `user.groups` to decide KB access; use
  `effective_group_ids()`.

Private article text goes to Vertex AI like public text: it is embedded for retrieval and
machine-translated.

## Listing and KB pages

`/knowledge-bases/` is the directory and `/knowledge-bases/<slug>/` a KB's page. A page
answers 404 unless the KB is in `browsable_by(user)`; the default KB and unknown slugs answer
the same way.

| `Audience.objects` | Returns | Staff bypass |
| --- | --- | --- |
| `listed_for(user)` | Menu, directory and search filter: listed public KBs, and listed private KBs with one of the viewer's groups | No, so Staff menus don't list every customer |
| `browsable_by(user)` | KB pages and the `kb=` search scope | Yes |
| `private_for(user)` | Private KBs the viewer can read, listed or not; the KBs they can upload private images to | Yes |
| `has_private_kb_access(user)` (function) | Whether the viewer can read any private KB | Yes |

`./manage.py add_product_articles_to_kb <product-slug> <kb-slug>` adds a KB to every
original of a product, keeping their other KBs.

## Search

With the `retrieval-hybrid-search` switch on:

- Private articles are in the retrieval index and returned only to their readers; every
  result is checked again in the database ([ADR 0006](architecture/decisions/0006-access-controlled-retrieval.md)).
- `kb=<slug>` scopes a search to that KB's articles. A KB outside `browsable_by(user)` is an
  invalid search parameter (form error, or 400 for JSON). A scoped search never falls back
  to broader results.
- An unscoped search by a viewer with private access starts page 1 with up to three
  matches from their own private KBs ("From <KB>" or "From your knowledge bases"); the main
  results leave those out. The block uses membership only, so Staff don't get every
  customer's articles.

With the switch off, search runs on the public-only legacy index: no private results, no KB
filter, and a scoped search returns nothing.

Search counts and snippets can lag an access change until the article is reindexed; the
database check keeps the article itself out.

## Private images

Every gallery image belongs to one KB, chosen at upload and fixed once the image is
finalized. Images uploaded as public go to the default KB.

- **Readers.** A private image is readable by Staff and superusers, members of its KB (by
  effective groups), and its creator while it is a draft; only while private storage is on.
- **Rendering.** `[[Image:title]]` in an article that is in exactly one private KB looks in
  that KB first, then in the default KB. Every other article, and forums and questions,
  look in the default KB only. A private image never renders outside its KB's articles, and
  an article in several private KBs can embed public images only.
- **Listings.** The gallery, its search and `/api/1/gallery/` are public-only for everyone,
  Staff included. The editor's picker lists a private KB's images to the people who can
  upload to it. On user-facing paths use `Image.objects.public()`, `private_in()`,
  `in_default_kb()` or `Image.is_readable_by(user)`, never a bare `Image.objects` query.
- **Titles** are unique per `(locale, title, KB)`, so a "title taken" error only ever
  concerns the uploader's own KB.
- **Bytes.** File names under `private/` go to the private storage, never the public bucket
  or CDN. The app serves them only at `/private-media/<name>`, after `is_readable_by`, with
  `Cache-Control: private, max-age=600`: a member who loses access can keep seeing an image
  they already loaded for ten minutes. Every failure is the same 404.
- **Making a KB public** makes its images readable by anyone who has their address, and
  they stop rendering in its articles, which then look in the default KB. Re-upload them as
  public images. The admin asks for confirmation when the KB has articles or images.

## Scheduled publishing

A reviewer can approve a revision with a publish time: a :00 or :30 slot in the reviewer's
timezone. The decision is stored in a `ScheduledRevision` (one per article), and the
revision itself stays unreviewed (`is_approved=False`, `reviewed=None`). Approved means live
in many places (current-revision promotion, `fix_current_revisions`, AI translation, l10n
readouts, emails), so a held revision marked approved would go live early through any one of
them.

- **Release.** `release_scheduled_revisions` runs at :00 and :30 (Celery beat) and applies
  the stored review as the reviewer, with every side effect of an ordinary approval. It
  first checks that the revision is still unreviewed and newer than the current one, and
  that the reviewer is active and can still review there; otherwise it drops the schedule
  and logs why. The approval and the schedule's deletion commit together, so a failed or
  missed run is caught up by the next one. Read-only mode skips it.
- **Held revisions** are visible only to their creator and to reviewers in the locale. For
  everyone else they are missing: 404, and absent from history, revision lists, compare,
  the review readouts and the weekly digest.
- Cancelling a schedule puts the revision back in the review queue. Approving a newer
  revision drops the held one's schedule.

Accepted tradeoffs, instead of a lock shared by every review action:

- A reviewer who rejects or reschedules at the moment the release applies the same
  revision can lose; it goes live.
- Two overlapping runs can approve one revision twice and send its emails twice.
- A failure after the approval commits leaves the article live with some emails, l10n
  fan-out or re-rendering skipped, as on the review page.
- A schedule whose release raises fails every run (Sentry) and holds back the schedules
  after it in that run, until someone cancels it.

## Settings

| Name | Meaning |
| --- | --- |
| `GS_PRIVATE_BUCKET_NAME` | GCS bucket for private images, with no public ACL and no CDN. Unset, or equal to `GS_BUCKET_NAME`, turns private images off. |
| `PRIVATE_MEDIA_ROOT` | Directory for private images when media is on the filesystem (dev, tests); outside `MEDIA_ROOT`. |
| `retrieval-hybrid-search` (waffle switch) | Hybrid search; private results, the KB filter and KB-scoped search need it. |

Private images are off on S3 storage and on GCS without a separate private bucket. Then
uploads to a private KB are rejected and existing private images answer 404 for everyone,
Staff included.

## In production

- **An article is visible only to Staff.** It has no KB. The Document admin's
  knowledge-base filter lists such articles; assign a KB.
- **A KB can't be deleted.** Articles or images still use it; the default KB can never be
  deleted.
- **A screenshot shows "The image … does not exist."** The article is in more than one
  private KB, the image belongs to another KB, its KB was made public, or private storage is
  off.
- **Every private image is a 404, even for Staff.** Private storage is off: check
  `GS_PRIVATE_BUCKET_NAME` on web and Celery.
- **A newly private article's title still shows to anonymous visitors.** Anonymous
  product/topic listings and curated blocks keep it until their cache expires (curated
  blocks: 24 hours); the article itself answers 404 at once.
- **A scheduled revision didn't go live.** Look for the "dropped" log line and its reason
  (reviewed, not newer than current, reviewer inactive or without permission), then approve
  it again.
