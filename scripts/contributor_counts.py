# Shows top posters and percentage of posts from top posters for the
# last 14 days. You need recent data to run this.
#
# Run this with ./manage.py runscript run_contributor_counts.py


from collections import defaultdict
from datetime import datetime, timedelta

from django.db.models.functions import Now

from kitsune.forums.models import Post


def run():
    two_weeks_ago = datetime.now() - timedelta(days=24)

    print(f"Data since {two_weeks_ago}")
    print("")

    # Use "__range" to ensure the database index is used in Postgres.
    query = Post.objects.filter(created__range=(two_weeks_ago, Now()))

    total_posts = query.count()

    posts_by_author = defaultdict(int)

    for post in query:
        username = post.author.username
        posts_by_author[username] = posts_by_author[username] + 1

    posts_by_author = sorted(list(posts_by_author.items()), key=lambda mem: -mem[1])

    top_posters = posts_by_author[:10]
    top_total = 0

    for name, count in top_posters:
        print(f"{name:>20}: {count}")
        top_total += count

    print("")
    print("Total posts:", total_posts)
    print("Top total:  ", top_total)
    print("Percent:    ", float(top_total) / float(total_posts))


if __name__ == "__main__":
    print('Run with "./manage.py runscript contributor_counts"')
