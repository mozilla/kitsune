#!/usr/bin/env python
import datetime
import subprocess
import sys
import textwrap
import urllib.error
import urllib.parse
import urllib.request

import requests


BUGZILLA_API_URL = "https://bugzilla.mozilla.org/rest/"
BUGZILLA_PRODUCT = "support.mozilla.org"

QUARTERS = {
    1: [(1, 1), (3, 31)],
    2: [(4, 1), (6, 30)],
    3: [(7, 1), (9, 30)],
    4: [(10, 1), (12, 31)],
}

USAGE = "Usage: in_review.py <YEAR> [<QUARTER>]"
HEADER = "in_review.py: find out what happened year or quarter!"

all_people = set()


def wrap(text, indent="    ", subsequent="    "):
    text = text.split("\n\n")
    text = [
        textwrap.fill(part, expand_tabs=True, initial_indent=indent, subsequent_indent=subsequent)
        for part in text
    ]
    return "\n\n".join(text)


def fetch(url):
    resp = requests.get(url)
    if resp.status_code != 200:
        raise Exception(resp.text)

    json_data = resp.json()

    if json_data.get("error"):
        raise Exception("ERROR " + repr(json_data))

    return json_data


def fetch_bugs(params):
    url = BUGZILLA_API_URL + "/bug" + "?" + urllib.parse.urlencode(params)
    return fetch(url)


def fetch_bug_history(bugid):
    url = BUGZILLA_API_URL + ("/bug/%d/history" % bugid)
    return fetch(url)


def fetch_bug_comments(bugid):
    url = BUGZILLA_API_URL + ("/bug/%d/comment" % bugid)
    return fetch(url)


def print_bugzilla_stats(from_date, to_date):
    # ------------------------------------------------
    # Bug creation stats
    # ------------------------------------------------
    params = {
        "product": BUGZILLA_PRODUCT,
        "f1": "creation_ts",
        "o1": "greaterthaneq",
        "v1": from_date.strftime("%Y-%m-%d"),
        "f2": "creation_ts",
        "o2": "lessthan",
        "v2": to_date.strftime("%Y-%m-%d"),
    }

    json_data = fetch_bugs(params)

    creation_count = len(json_data["bugs"])

    creators = {}
    for bug in json_data["bugs"]:
        creator = bug["creator_detail"]["real_name"]
        if not creator:
            creator = bug["creator"].split("@")[0]
        creators[creator] = creators.get(creator, 0) + 1
        all_people.add(creator)

    print("Bugs created: %s" % creation_count)
    print("Creators: %s" % len(creators))
    print("")
    creators = sorted(list(creators.items()), reverse=True, key=lambda item: item[1])
    for person, count in creators:
        print(" %34s : %s" % (person[:30].encode("utf-8"), count))
    print("")

    # ------------------------------------------------
    # Bug resolution stats
    # ------------------------------------------------
    params = {
        "product": BUGZILLA_PRODUCT,
        "f1": "cf_last_resolved",
        "o1": "greaterthaneq",
        "v1": from_date.strftime("%Y-%m-%d"),
        "f2": "cf_last_resolved",
        "o2": "lessthan",
        "v2": to_date.strftime("%Y-%m-%d"),
    }

    json_data = fetch_bugs(params)

    resolved_count = len(json_data["bugs"])
    resolved_map = {}
    resolvers = {}
    traceback_bugs = []
    research_bugs = []
    tracker_bugs = []
    commenters = {}

    for bug in json_data["bugs"]:
        summary = bug["summary"].lower()
        if summary.startswith("[traceback]"):
            traceback_bugs.append(bug)
        elif summary.startswith("[research]"):
            research_bugs.append(bug)
        elif summary.startswith("[tracker]"):
            tracker_bugs.append(bug)

        history = fetch_bug_history(bug["id"])

        resolution = bug["resolution"]
        resolved_map[resolution] = resolved_map.get(resolution, 0) + 1
        assigned = bug["assigned_to_detail"]["real_name"]
        if not assigned:
            assigned = bug["assigned_to"].split("@")[0]

        if "nobody" in assigned.lower():
            # If no one was assigned, we give "credit" to whoever
            # triaged the bug. We go through the history in reverse
            # order because the "resolver" is the last person to
            # resolve the bug.
            for item in reversed(history["bugs"][0]["history"]):
                # See if this item in the history is the resolving event.
                # If it is, then we know who resolved the bug and we
                # can stop looking at history.
                changes = [
                    change
                    for change in item["changes"]
                    if change["field_name"] == "status" and change["added"] == "RESOLVED"
                ]

                if not changes:
                    continue

                assigned = item["who"]
                break

        if assigned:
            if "@" in assigned:
                assigned = assigned.split("@")[0]

            resolvers[assigned] = resolvers.get(assigned, 0) + 1
            all_people.add(assigned)

        # Now get all the commenters
        comments = fetch_bug_comments(bug["id"])
        # The Bugzilla REST api has some interesting things about it.
        for comment in comments["bugs"][str(bug["id"])]["comments"]:
            commenter = comment["author"]
            if "@" in commenter:
                commenter = commenter.split("@")[0]

            commenters[commenter] = commenters.get(commenter, 0) + 1
            all_people.add(commenter)

    print("Bugs resolved: %s" % resolved_count)
    print("")
    for resolution, count in list(resolved_map.items()):
        print(" %34s : %s" % (resolution, count))

    print("")
    for title, count in [
        ("Tracebacks", len(traceback_bugs)),
        ("Research", len(research_bugs)),
        ("Tracker", len(tracker_bugs)),
    ]:
        print(" %34s : %s" % (title, count))

    print("")
    print("Research bugs: %s" % len(research_bugs))
    print("")
    for bug in research_bugs:
        print(wrap("%s: %s" % (bug["id"], bug["summary"]), subsequent="        "))

    print("")
    print("Tracker bugs: %s" % len(tracker_bugs))
    print("")
    for bug in tracker_bugs:
        print(wrap("%s: %s" % (bug["id"], bug["summary"]), subsequent="        "))

    print("")
    print("Resolvers: %s" % len(resolvers))
    print("")
    resolvers = sorted(list(resolvers.items()), reverse=True, key=lambda item: item[1])
    for person, count in resolvers:
        print(" %34s : %s" % (person[:30].encode("utf-8"), count))

    print("")
    print("Commenters: %s" % len(commenters))
    print("")
    commenters = sorted(list(commenters.items()), reverse=True, key=lambda item: item[1])
    for person, count in commenters:
        print(" %34s : %s" % (person[:30].encode("utf-8"), count))


def git(*args):
    return subprocess.check_output(args)


def print_git_stats(from_date, to_date):
    all_commits = subprocess.check_output(
        [
            "git",
            "log",
            "--after=" + from_date.strftime("%Y-%m-%d"),
            "--before=" + to_date.strftime("%Y-%m-%d"),
            "--format=%H",
        ]
    )

    all_commits = all_commits.splitlines()

    # Person -> # commits
    committers = {}

    # Person -> (# files changed, # inserted, # deleted)
    changes = {}

    for commit in all_commits:
        author = git("git", "show", "-s", "--format=%an", commit)
        author = author.strip().decode("utf-8")

        committers[author] = committers.get(author, 0) + 1
        all_people.add(author)

        diff_data = git(
            "git", "show", "--numstat", "--format=oneline", "--find-copies-harder", commit
        )
        total_added = 0
        total_deleted = 0
        total_files = 0

        # Skip the first line because it's the oneline summary and that's
        # not part of the numstat data we want.
        lines = diff_data.splitlines()[1:]
        for line in lines:
            if not line:
                continue
            added, deleted, fn = line.split("\t")
            if fn.startswith("vendor/"):
                continue
            if added != "-":
                total_added += int(added)
            if deleted != "-":
                total_deleted += int(deleted)
            total_files += 1

        old_changes = changes.get(author, (0, 0, 0))
        changes[author] = (
            old_changes[0] + total_added,
            old_changes[1] + total_deleted,
            old_changes[2] + total_files,
        )

    print("Total commits:", len(all_commits))
    print("")

    committers = sorted(list(committers.items()), key=lambda item: item[1], reverse=True)
    for person, count in committers:
        print(
            "  %20s : %5s  (+%s, -%s, files %s)"
            % (
                person.encode("utf-8"),
                count,
                changes[person][0],
                changes[person][1],
                changes[person][2],
            )
        )
        all_people.add(person)

    # This is goofy summing, but whatevs.
    print("")
    print("Total lines added:", sum([item[0] for item in list(changes.values())]))
    print("Total lines deleted:", sum([item[1] for item in list(changes.values())]))
    print("Total files changed:", sum([item[2] for item in list(changes.values())]))


def print_all_people():
    # We do this sorting thing to make it a little easier to suss out
    # duplicates since we're pulling names from three different forms
    # between Bugzilla and git. You're still going to have to go
    # through it by hand to remove duplicates.
    people = sorted(all_people, key=lambda a: a.lower())

    for person in people:
        print("    %s" % person.encode("utf-8"))


def print_header(text):
    print("")
    print(text)
    print("=" * len(text))
    print("")


def main(argv):
    # XXX: This helps debug bugzilla xmlrpc bits.
    # logging.basicConfig(level=logging.DEBUG)

    if len(argv) < 1:
        print(USAGE)
        print("Error: Must specify year or year and quarter. Examples:")
        print("in_review.py 2014")
        print("in_review.py 2014 1")
        return 1

    print(HEADER)

    year = int(argv[0])
    if len(argv) == 1:
        from_date = datetime.date(year, 1, 1)
        to_date = datetime.date(year, 12, 31)

        print_header("Year %s (%s -> %s)" % (year, from_date, to_date))

    else:
        quarter = int(argv[1])
        quarter_dates = QUARTERS[quarter]

        from_date = datetime.date(year, quarter_dates[0][0], quarter_dates[0][1])
        to_date = datetime.date(year, quarter_dates[1][0], quarter_dates[1][1])

        print_header("Quarter %sq%s (%s -> %s)" % (year, quarter, from_date, to_date))

    # Add 1 day because we do less-than.
    to_date = to_date + datetime.timedelta(days=1)

    print_header("Bugzilla")
    print_bugzilla_stats(from_date, to_date)

    print_header("git")
    print_git_stats(from_date, to_date)

    print_header("Everyone")
    print_all_people()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
