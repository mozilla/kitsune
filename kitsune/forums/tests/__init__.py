from datetime import datetime

import factory
from django.contrib.contenttypes.models import ContentType
from django.template.defaultfilters import slugify

from kitsune.access.tests import PermissionFactory
from kitsune.forums.models import Forum, Post, Thread
from kitsune.sumo.tests import FuzzyUnicode, LocalizingClient, TestCase
from kitsune.users.tests import UserFactory


class ForumTestCase(TestCase):
    client_class = LocalizingClient


class ForumFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Forum

    name = FuzzyUnicode()
    slug = factory.LazyAttribute(lambda o: slugify(o.name))


class RestrictedForumFactory(ForumFactory):
    @factory.post_generation
    def permission_code(forum, created, extracted, **kwargs):
        assert created
        permission = extracted or "forums_forum.view_in_forum"
        ct = ContentType.objects.get_for_model(forum)
        PermissionFactory(codename=permission, content_type=ct, object_id=forum.id)


class ThreadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Thread

    created = factory.LazyAttribute(lambda t: datetime.now())
    creator = factory.SubFactory(UserFactory)
    forum = factory.SubFactory(ForumFactory)
    title = FuzzyUnicode()

    @factory.post_generation
    def posts(obj, create, extracted, **kwargs):
        defaults = {
            "created": obj.created,
            "author": obj.creator,
            "thread": obj,
        }
        defaults.update(**kwargs)

        if extracted is None:
            posts = [PostFactory(**defaults)]
        else:
            posts = []
            for args in extracted:
                args.update(defaults)
                posts.append(PostFactory(**args))

        for post in posts:
            obj.post_set.add(post)


class ThreadFactoryTests(TestCase):
    def test_has_one_post(self):
        t = ThreadFactory()
        self.assertEqual(t.post_set.count(), 1)

    def test_can_set_post_properties(self):
        t = ThreadFactory(posts__content="lol")
        self.assertEqual(t.post_set.get().content, "lol")

    def test_can_set_posts(self):
        t = ThreadFactory(posts=[{"content": "one"}, {"content": "two"}])
        contents = list(t.post_set.values_list("content", flat=True))
        self.assertEqual(contents, ["one", "two"])

    def test_posts_belong_to_the_thread(self):
        t = ThreadFactory()
        assert all(p.thread == t for p in t.post_set.all())
        t = ThreadFactory(posts=[{}, {}, {}])
        assert all(p.thread == t for p in t.post_set.all())
        t = ThreadFactory(posts=[{"content": "two"}, {"content": "one"}])
        assert all(p.thread == t for p in t.post_set.all())


class PostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    author = factory.SubFactory(UserFactory)
    thread = factory.SubFactory(ThreadFactory, creator=factory.SelfAttribute("..author"), posts=[])

    @classmethod
    def _create(cls, model_class, *args, **kwargs):
        obj = model_class(*args, **kwargs)
        obj.save()
        return obj
