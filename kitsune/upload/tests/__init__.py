import factory

from kitsune.questions.tests import QuestionFactory
from kitsune.sumo.tests import TestCase
from kitsune.upload.models import ImageAttachment
from kitsune.upload.storage import RenameFileStorage
from kitsune.users.tests import UserFactory


class ImageAttachmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ImageAttachment

    creator = factory.SubFactory(UserFactory)
    content_object = factory.SubFactory(QuestionFactory)
    file = factory.django.FileField()


def check_file_info(file_info, name, width, height, delete_url, url, thumbnail_url):
    tc = TestCase()
    tc.assertEqual(name, file_info["name"])
    tc.assertEqual(width, file_info["width"])
    tc.assertEqual(height, file_info["height"])
    tc.assertEqual(delete_url, file_info["delete_url"])
    tc.assertEqual(url, file_info["url"])
    tc.assertEqual(thumbnail_url, file_info["thumbnail_url"])


def get_file_name(name):
    storage = RenameFileStorage()
    return storage.get_available_name(name)
