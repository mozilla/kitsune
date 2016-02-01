from django import template
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.contrib.auth.models import AnonymousUser

from authority import get_check
from authority import permissions
from authority.compat import get_user_model
from authority.models import Permission
from authority.forms import UserPermissionForm


User = get_user_model()
register = template.Library()


@register.simple_tag
def url_for_obj(view_name, obj):
    return reverse(view_name, kwargs={
        'app_label': obj._meta.app_label,
        'module_name': obj._meta.module_name,
        'pk': obj.pk}
    )


@register.simple_tag
def add_url_for_obj(obj):
    return url_for_obj('authority-add-permission', obj)


@register.simple_tag
def request_url_for_obj(obj):
    return url_for_obj('authority-add-permission-request', obj)


class ResolverNode(template.Node):
    """
    A small wrapper that adds a convenient resolve method.
    """
    def resolve(self, var, context):
        """Resolves a variable out of context if it's not in quotes"""
        if var is None:
            return var
        if var[0] in ('"', "'") and var[-1] == var[0]:
            return var[1:-1]
        else:
            return template.Variable(var).resolve(context)

    @classmethod
    def next_bit_for(cls, bits, key, if_none=None):
        try:
            return bits[bits.index(key)+1]
        except ValueError:
            return if_none


class PermissionComparisonNode(ResolverNode):
    """
    Implements a node to provide an "if user/group has permission on object"
    """
    @classmethod
    def handle_token(cls, parser, token):
        bits = token.contents.split()
        if 5 < len(bits) < 3:
            raise template.TemplateSyntaxError(
                "'%s' tag takes three, "
                "four or five arguments" % bits[0]
            )
        end_tag = 'endifhasperm'
        nodelist_true = parser.parse(('else', end_tag))
        token = parser.next_token()
        if token.contents == 'else':  # there is an 'else' clause in the tag
            nodelist_false = parser.parse((end_tag,))
            parser.delete_first_token()
        else:
            nodelist_false = template.NodeList()
        if len(bits) == 3:  # this tag requires at most 2 objects . None is given
            objs = (None, None)
        elif len(bits) == 4:  # one is given
            objs = (bits[3], None)
        else:  # two are given
            objs = (bits[3], bits[4])
        return cls(bits[2], bits[1], nodelist_true, nodelist_false, *objs)

    def __init__(self, user, perm, nodelist_true, nodelist_false, *objs):
        self.user = user
        self.objs = objs
        self.perm = perm
        self.nodelist_true = nodelist_true
        self.nodelist_false = nodelist_false

    def render(self, context):
        try:
            user = self.resolve(self.user, context)
            perm = self.resolve(self.perm, context)
            if self.objs:
                objs = []
                for obj in self.objs:
                    if obj is not None:
                        objs.append(self.resolve(obj, context))
            else:
                objs = None
            check = get_check(user, perm)
            if check is not None:
                if check(*objs):
                    # return True if check was successful
                    return self.nodelist_true.render(context)
        # If the app couldn't be found
        except (ImproperlyConfigured, ImportError):
            return ''
        # If either variable fails to resolve, return nothing.
        except template.VariableDoesNotExist:
            return ''
        # If the types don't permit comparison, return nothing.
        except (TypeError, AttributeError):
            return ''
        return self.nodelist_false.render(context)


@register.tag
def ifhasperm(parser, token):
    """
    This function provides functionality for the 'ifhasperm' template tag

    Syntax::

        {% ifhasperm PERMISSION_LABEL.CHECK_NAME USER *OBJS %}
            lalala
        {% else %}
            meh
        {% endifhasperm %}

        {% ifhasperm "poll_permission.change_poll" request.user %}
            lalala
        {% else %}
            meh
        {% endifhasperm %}

    """
    return PermissionComparisonNode.handle_token(parser, token)


class PermissionFormNode(ResolverNode):

    @classmethod
    def handle_token(cls, parser, token, approved):
        bits = token.contents.split()
        kwargs = {
            'obj': cls.next_bit_for(bits, 'for'),
            'perm': cls.next_bit_for(bits, 'using', None),
            'template_name': cls.next_bit_for(bits, 'with', ''),
            'approved': approved,
        }
        return cls(**kwargs)

    def __init__(self, obj, perm=None, approved=False, template_name=None):
        self.obj = obj
        self.perm = perm
        self.approved = approved
        self.template_name = template_name

    def render(self, context):
        obj = self.resolve(self.obj, context)
        perm = self.resolve(self.perm, context)
        if self.template_name:
            template_name = [self.resolve(o, context) for o in self.template_name.split(',')]
        else:
            template_name = 'authority/permission_form.html'
        request = context['request']
        extra_context = {}
        if self.approved:
            if (request.user.is_authenticated() and
                    request.user.has_perm('authority.add_permission')):
                extra_context = {
                    'form_url': url_for_obj('authority-add-permission', obj),
                    'next': request.build_absolute_uri(),
                    'approved': self.approved,
                    'form': UserPermissionForm(perm, obj, approved=self.approved,
                                               initial=dict(codename=perm)),
                }
        else:
            if request.user.is_authenticated() and not request.user.is_superuser:
                extra_context = {
                    'form_url': url_for_obj('authority-add-permission-request', obj),
                    'next': request.build_absolute_uri(),
                    'approved': self.approved,
                    'form': UserPermissionForm(
                        perm,
                        obj,
                        approved=self.approved,
                        initial=dict(codename=perm, user=request.user.username)),
                }
        return template.loader.render_to_string(
            template_name, extra_context, context_instance=template.RequestContext(request))


@register.tag
def permission_form(parser, token):
    """
    Renders an "add permissions" form for the given object. If no object
    is given it will render a select box to choose from.

    Syntax::

        {% permission_form for OBJ using PERMISSION_LABEL.CHECK_NAME [with TEMPLATE] %}
        {% permission_form for lesson using "lesson_permission.add_lesson" %}

    """
    return PermissionFormNode.handle_token(parser, token, approved=True)


@register.tag
def permission_request_form(parser, token):
    """
    Renders an "add permissions" form for the given object. If no object
    is given it will render a select box to choose from.

    Syntax::

        {% permission_request_form for OBJ and PERMISSION_LABEL.CHECK_NAME [with TEMPLATE] %}
        {% permission_request_form for lesson using "lesson_permission.add_lesson"
            with "authority/permission_request_form.html" %}

    """
    return PermissionFormNode.handle_token(parser, token, approved=False)


class PermissionsForObjectNode(ResolverNode):

    @classmethod
    def handle_token(cls, parser, token, approved, name):
        bits = token.contents.split()
        tag_name = bits[0]
        kwargs = {
            'obj': cls.next_bit_for(bits, tag_name),
            'user': cls.next_bit_for(bits, 'for'),
            'var_name': cls.next_bit_for(bits, 'as', name),
            'approved': approved,
        }
        return cls(**kwargs)

    def __init__(self, obj, user, var_name, approved, perm=None):
        self.obj = obj
        self.user = user
        self.perm = perm
        self.var_name = var_name
        self.approved = approved

    def render(self, context):
        obj = self.resolve(self.obj, context)
        var_name = self.resolve(self.var_name, context)
        user = self.resolve(self.user, context)
        perms = []
        if not isinstance(user, AnonymousUser):
            perms = Permission.objects.for_object(obj, self.approved)
            if isinstance(user, User):
                perms = perms.filter(user=user)
        context[var_name] = perms
        return ''


@register.tag
def get_permissions(parser, token):
    """
    Retrieves all permissions associated with the given obj and user
    and assigns the result to a context variable.

    Syntax::

        {% get_permissions obj %}
        {% for perm in permissions %}
            {{ perm }}
        {% endfor %}

        {% get_permissions obj as "my_permissions" %}
        {% get_permissions obj for request.user as "my_permissions" %}

    """
    return PermissionsForObjectNode.handle_token(parser, token, approved=True,
                                                 name='"permissions"')


@register.tag
def get_permission_requests(parser, token):
    """
    Retrieves all permissions requests associated with the given obj and user
    and assigns the result to a context variable.

    Syntax::

        {% get_permission_requests obj %}
        {% for perm in permissions %}
            {{ perm }}
        {% endfor %}

        {% get_permission_requests obj as "my_permissions" %}
        {% get_permission_requests obj for request.user as "my_permissions" %}

    """
    return PermissionsForObjectNode.handle_token(parser, token,
                                                 approved=False,
                                                 name='"permission_requests"')


class PermissionForObjectNode(ResolverNode):

    @classmethod
    def handle_token(cls, parser, token, approved, name):
        bits = token.contents.split()
        tag_name = bits[0]
        kwargs = {
            'perm': cls.next_bit_for(bits, tag_name),
            'user': cls.next_bit_for(bits, 'for'),
            'objs': cls.next_bit_for(bits, 'and'),
            'var_name': cls.next_bit_for(bits, 'as', name),
            'approved': approved,
        }
        return cls(**kwargs)

    def __init__(self, perm, user, objs, approved, var_name):
        self.perm = perm
        self.user = user
        self.objs = objs
        self.var_name = var_name
        self.approved = approved

    def render(self, context):
        objs = [self.resolve(obj, context) for obj in self.objs.split(',')]
        var_name = self.resolve(self.var_name, context)
        perm = self.resolve(self.perm, context)
        user = self.resolve(self.user, context)
        granted = False
        if not isinstance(user, AnonymousUser):
            if self.approved:
                check = get_check(user, perm)
                if check is not None:
                    granted = check(*objs)
            else:
                check = permissions.BasePermission(user=user)
                for obj in objs:
                    granted = check.requested_perm(perm, obj)
                    if granted:
                        break
        context[var_name] = granted
        return ''


@register.tag
def get_permission(parser, token):
    """
    Performs a permission check with the given signature, user and objects
    and assigns the result to a context variable.

    Syntax::

        {% get_permission PERMISSION_LABEL.CHECK_NAME for USER and *OBJS [as VARNAME] %}

        {% get_permission "poll_permission.change_poll"
            for request.user and poll as "is_allowed" %}
        {% get_permission "poll_permission.change_poll"
            for request.user and poll,second_poll as "is_allowed" %}

        {% if is_allowed %}
            I've got ze power to change ze pollllllzzz. Muahahaa.
        {% else %}
            Meh. No power for meeeee.
        {% endif %}

    """
    return PermissionForObjectNode.handle_token(parser, token,
                                                approved=True,
                                                name='"permission"')


@register.tag
def get_permission_request(parser, token):
    """
    Performs a permission request check with the given signature, user and objects
    and assigns the result to a context variable.

    Syntax::

        {% get_permission_request PERMISSION_LABEL.CHECK_NAME for USER and *OBJS [as VARNAME] %}

        {% get_permission_request "poll_permission.change_poll"
            for request.user and poll as "asked_for_permissio" %}
        {% get_permission_request "poll_permission.change_poll"
            for request.user and poll,second_poll as "asked_for_permissio" %}

        {% if asked_for_permissio %}
            Dude, you already asked for permission!
        {% else %}
            Oh, please fill out this 20 page form and sign here.
        {% endif %}

    """
    return PermissionForObjectNode.handle_token(
        parser, token, approved=False, name='"permission_request"')


def base_link(context, perm, view_name):
    return {
        'next': context['request'].build_absolute_uri(),
        'url': reverse(view_name, kwargs={'permission_pk': perm.pk}),
    }


@register.inclusion_tag('authority/permission_delete_link.html', takes_context=True)
def permission_delete_link(context, perm):
    """
    Renders a html link to the delete view of the given permission. Returns
    no content if the request-user has no permission to delete foreign
    permissions.
    """
    user = context['request'].user
    if user.is_authenticated():
        if (user.has_perm('authority.delete_foreign_permissions') or
                user.pk == perm.creator.pk):
            return base_link(context, perm, 'authority-delete-permission')
    return {'url': None}


@register.inclusion_tag('authority/permission_request_delete_link.html', takes_context=True)
def permission_request_delete_link(context, perm):
    """
    Renders a html link to the delete view of the given permission request.
    Returns no content if the request-user has no permission to delete foreign
    permissions.
    """
    user = context['request'].user
    if user.is_authenticated():
        link_kwargs = base_link(context, perm,
                                'authority-delete-permission-request')
        if user.has_perm('authority.delete_permission'):
            link_kwargs['is_requestor'] = False
            return link_kwargs
        if not perm.approved and perm.user == user:
            link_kwargs['is_requestor'] = True
            return link_kwargs
    return {'url': None}


@register.inclusion_tag('authority/permission_request_approve_link.html', takes_context=True)
def permission_request_approve_link(context, perm):
    """
    Renders a html link to the approve view of the given permission request.
    Returns no content if the request-user has no permission to delete foreign
    permissions.
    """
    user = context['request'].user
    if user.is_authenticated():
        if user.has_perm('authority.approve_permission_requests'):
            return base_link(context, perm, 'authority-approve-permission-request')
    return {'url': None}
