from inspect import getmembers, ismethod
from django.db import models
from django.db.models.base import ModelBase
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ImproperlyConfigured

from authority.permissions import BasePermission


class AlreadyRegistered(Exception):
    pass


class NotRegistered(Exception):
    pass


class PermissionSite(object):
    """
    A dictionary that contains permission instances and their labels.
    """
    _registry = {}
    _choices = {}

    def get_permission_by_label(self, label):
        for perm_cls in self._registry.values():
            if perm_cls.label == label:
                return perm_cls
        return None

    def get_permissions_by_model(self, model):
        return [perm for perm in self._registry.values() if perm.model == model]

    def get_check(self, user, label):
        perm_label, check_name = label.split('.')
        perm_cls = self.get_permission_by_label(perm_label)
        if perm_cls is None:
            return None
        perm_instance = perm_cls(user)
        return getattr(perm_instance, check_name, None)

    def get_labels(self):
        return [perm.label for perm in self._registry.values()]

    def get_choices_for(self, obj, default=models.BLANK_CHOICE_DASH):
        model_cls = obj
        if not isinstance(obj, ModelBase):
            model_cls = obj.__class__
        if model_cls in self._choices:
            return self._choices[model_cls]
        choices = [] + default
        for perm in self.get_permissions_by_model(model_cls):
            for name, check in getmembers(perm, ismethod):
                if name in perm.checks:
                    signature = '%s.%s' % (perm.label, name)
                    label = getattr(check, 'short_description', signature)
                    choices.append((signature, label))
        self._choices[model_cls] = choices
        return choices

    def register(self, model_or_iterable, permission_class=None, **options):
        if not permission_class:
            permission_class = BasePermission

        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]

        if permission_class.label in self.get_labels():
            raise ImproperlyConfigured(
                "The name of %s conflicts with %s" % (
                    permission_class, self.get_permission_by_label(permission_class.label)))

        for model in model_or_iterable:
            if model in self._registry:
                raise AlreadyRegistered(
                    'The model %s is already registered' % model.__name__)
            if options:
                options['__module__'] = __name__
                permission_class = type(
                    "%sPermission" % model.__name__, (permission_class,), options)

            permission_class.model = model
            self.setup(model, permission_class)
            self._registry[model] = permission_class

    def unregister(self, model_or_iterable):
        if isinstance(model_or_iterable, ModelBase):
            model_or_iterable = [model_or_iterable]
        for model in model_or_iterable:
            if model not in self._registry:
                raise NotRegistered('The model %s is not registered' % model.__name__)
            del self._registry[model]

    def setup(self, model, permission):
        for check_name in permission.checks:
            check_func = getattr(permission, check_name, None)
            if check_func is not None:
                func = self.create_check(check_name, check_func)
                func.__name__ = check_name
                func.short_description = getattr(
                    check_func,
                    'short_description',
                    _("%(object_name)s permission '%(check)s'") % {
                        'object_name': model._meta.object_name,
                        'check': check_name})
                setattr(permission, check_name, func)
            else:
                permission.generic_checks.append(check_name)
        for check_name in permission.generic_checks:
            func = self.create_check(check_name, generic=True)
            object_name = model._meta.object_name
            func_name = "%s_%s" % (check_name, object_name.lower())
            func.short_description = _("Can %(check)s this %(object_name)s") % {
                'object_name': model._meta.object_name.lower(),
                'check': check_name}
            func.check_name = check_name
            if func_name not in permission.checks:
                permission.checks = (list(permission.checks) + [func_name])
            setattr(permission, func_name, func)
        setattr(model, "permissions", PermissionDescriptor())

    def create_check(self, check_name, check_func=None, generic=False):
        def check(self, *args, **kwargs):
            granted = self.can(check_name, generic, *args, **kwargs)
            if check_func and not granted:
                return check_func(self, *args, **kwargs)
            return granted
        return check


class PermissionDescriptor(object):
    def get_content_type(self, obj=None):
        ContentType = models.get_model("contenttypes", "contenttype")
        if obj:
            return ContentType.objects.get_for_model(obj)
        else:
            raise Exception("Invalid arguments given to PermissionDescriptor.get_content_type")

    def __get__(self, instance, owner):
        if instance is None:
            return self
        ct = self.get_content_type(instance)
        return ct.row_permissions.all()

site = PermissionSite()
get_check = site.get_check
get_choices_for = site.get_choices_for
register = site.register
unregister = site.unregister
