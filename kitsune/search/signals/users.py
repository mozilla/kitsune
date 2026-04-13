from django.contrib.auth.models import Group, User
from django.db.models.signals import m2m_changed, post_delete, post_save

from kitsune.products.models import Product
from kitsune.search.decorators import search_receiver
from kitsune.search.es_utils import delete_object, index_object, remove_from_field
from kitsune.users.models import Profile


@search_receiver(post_save, User)
@search_receiver(post_save, Profile)
@search_receiver(m2m_changed, User.groups.through)
@search_receiver(m2m_changed, Profile.products.through)
def handle_profile_save(instance, **kwargs):
    index_object.delay("ProfileDocument", instance.pk)


@search_receiver(post_delete, Profile)
def handle_profile_delete(instance, **kwargs):
    delete_object.delay("ProfileDocument", instance.pk)


@search_receiver(post_delete, Group)
def handle_group_delete(instance, **kwargs):
    remove_from_field.delay("ProfileDocument", "group_ids", instance.pk)


@search_receiver(post_delete, Product)
def handle_product_delete(instance, **kwargs):
    remove_from_field.delay("ProfileDocument", "product_ids", instance.pk)
