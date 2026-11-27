# Official UI labels

A Knowledge Base article often names a menu, a button or another part of a user interface
(UI). That can be the interface of an app, a website or an operating system. The article
writes the name inside `{menu …}`, `{button …}` or `{pref …}`, as in `Click {menu Settings}`.

A translated article should say what its reader's screen says. If Firefox shows "Paramètres"
in French, the French article must say `{menu Paramètres}`, and not another fair translation
such as "Réglages".

This feature finds how each product itself translates those names, and makes machine
translations use them. It is part of the [AI localization system](l10n-system.md). Machine
translations use it only once the waffle switch `official-ui-labels` is created and turned
on. The daily sync and the report work without the switch.

The code is in `kitsune/llm/l10n/ui_labels/`. Its package docstring defines the words used
below, and `kitsune/llm/CLAUDE.md` has notes for working in it.

## The words we use

A **label** is the text inside the markup, like "Settings". Its **official label** is how the
product shows it in one locale, like "Paramètres". The **owner** of a label is the app or
website whose screen shows it, such as Firefox, Thunderbird or addons.mozilla.org.

Products keep their text as **strings**, each with an ID and a translation per locale. A
**source** is a repository that holds strings, and a **catalog** is all of one owner's strings
in one locale.

A **spot** matters when a product uses the same English text in several places. Firefox has
"View" in its menu bar, on a button for crash reports and in the password manager. French
translates these as "Affichage", "Afficher" and "Voir". Strings that share their English text
and are translated alike in every locale form one spot. So "View" in Firefox has several
spots, and someone has to read the article to tell which one a label means.

## How it works

```
GitHub ──► daily sync ──► catalogs and spot lists ─┐
                                                   ├─► official label ──► machine translation
English revision ──► LLM ──► owner of each label ──┘                  └─► report
```

### The daily sync

Every day at 05:00 the task `sync_ui_strings` starts one task for each source. A source is
downloaded only when something about it changed, and its strings are saved as catalogs, for
English and for each locale the owner really ships. An hour later `build_ui_spot_lists` groups
each owner's strings into spots.

A source that fails keeps the strings from its last good sync. The error is saved on the
source, shown in the admin, and reported to Sentry.

### Finding a label's owner

The text alone can't say who owns a label. "Settings" is in Firefox, in Thunderbird and in
Windows. So a large language model (LLM) reads the whole English article once and names the
owner of every label. Where the owner has several spots for the text, and the article is about
one of that owner's products, it also chooses the spot. A label on another program's screen
gets the owner "unknown", with a reason such as "os" or "website".

The answers are saved for that revision and reused by every locale. A new revision is asked
about again, because a change anywhere in an article can change what a label means. A saved
answer is also asked for again when the question or the model changes, or when a sync changes
the spot it names.

### Choosing the official label

With the owner known, these rules settle the official label, in this order:

1. The translated article already has one of the owner's official labels for this text, and
   the spot doesn't name another one. It is kept.
2. The owner has only one translation of the text. That one is used.
3. The LLM chose a spot. The spot's translation is used.
4. Otherwise it is unclear, and the label gets no official label.

A label has no official label when its owner is unknown, when the owner has no string with
that text, when the owner doesn't ship the locale or shows English in it, or when the owner's
strings are not synced yet.

### In a machine translation

Before the LLM translates an article, it is given the official label for each label that has
one, and told to write exactly that. A label that gets different official labels within one
article, like "General" in Firefox and then in Windows, is left for the check. The LLM is also
told to leave config text as it is, like a preference's name inside `{pref …}`.

Afterwards a check reads the translation. A label that the LLM left in English, or gave the
official label of another spot, gets the right one. Nothing else in the text is touched.

The explanation that staff can read with each machine translation says what happened:

```
UI labels: 2 of 3 have an official label.
{menu Settings} → Paramètres (firefox, the only translation)
{menu View} → Affichage (firefox, one of 4 official labels, chosen by spot browser/browser/menubar.ftl:menu-view.label)
{button Open} has no official label (unknown: os)
```

A problem in this feature never costs an article its translation. The error goes to Sentry,
and the article is translated as it would be with the switch off.

## Checking existing translations

The report compares the labels in translations with the official labels. It changes no
article. It checks a translation only when it was made from the English article's latest
revision that is ready for localization. Any other is listed as out of date.

```bash
./manage.py ui_labels report --locale fr,de --output report.csv
```

It prints a count per locale and can write every finding to a CSV file. The findings include
"matches the official label", "left in English" and "differs from the official label".

The report uses the LLM. It asks for the label owners of each English revision that has none
saved. It also asks the LLM to match a translated label to its English label when their text
alone doesn't.

## In the admin

Three pages in the `llm` section of the Django admin help when an official label looks
wrong:

- **UI string sources** shows each source's last sync and its error, if it had one.
- **UI label owners** shows the owner and spot chosen for each label of an English revision.
- **UI label pairs** shows which English label each label of a translation stands for, with
  the LLM's explanation.

The last two are found by a revision's ID or by the article's title or slug.

## Turning it on

Create the waffle switch `official-ui-labels` and turn it on. Two settings are optional:
`UI_LABELS_GITHUB_TOKEN` raises GitHub's limit on requests, and `UI_LABELS_GITHUB_TIMEOUT`
sets how long a download may take to connect and to answer.

After the first deploy, run the `sync_ui_strings` task a second time once the first run has
finished. Thunderbird and Firefox Enterprise use strings from Firefox's repositories with
their own brand names, and the second run fills in any that the first one read before those
names were saved.

## When you change something

Strings and LLM answers are saved and reused. So you must raise a version number before a
change takes effect:

- After changing how strings are read, raise `PARSER_VERSION` in `strings/sync.py`.
- After changing the owner question, the list of owners, or the fields of `LabelOwner`, raise
  `QUESTION_VERSION` in `owners/prompt.py`.
- After changing the pairing question, raise `QUESTION_VERSION` in `pairing.py`.

To add an owner, add it to `owners/__init__.py`, its files to `strings/sources.py`, and its
list of shipped locales to `strings/shipped_locales.py`. Then raise `QUESTION_VERSION` in
`owners/prompt.py`, so that labels saved as "unknown" are asked about again.

## Limits to know about

- The LLM can name a different owner on another day for an article that is truly unclear, such
  as one about an add-on's menus inside Thunderbird. The answer a revision gets first is the
  one that is kept.
- In Korean, Turkish, Tamil and Telugu, an ending attached to a label depends on how the label
  sounds. The check leaves such a label alone and lists it for staff.
- A label that the LLM translated in its own words is not corrected by the check. It is listed
  for staff as an official label that the translation doesn't use.
