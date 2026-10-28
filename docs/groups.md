# Groups System

Hierarchical groups of users with configurable visibility, sibling isolation, and delegated
leadership. Groups:

- **restrict content** (wiki articles, questions, and more) to their members;
- **delegate moderation** to leaders who manage members and content;
- **nest** in parent-child hierarchies;
- **isolate** sibling groups from discovering each other.

Enterprise companies are built on groups; see [Enterprise support](enterprise-support.md).

## Architecture

Groups use django-treebeard's materialized paths (`MP_Node`): any depth (3–4 levels
recommended), exactly one parent per group, and path-based ancestor and descendant queries.

```
Organization (root)
├── GroupA
│   ├── SubgroupX
│   └── SubgroupY
└── GroupB
    └── SubgroupZ
```

- `TreeModelBase` (`kitsune.groups.models`): abstract base combining `MP_Node` and Kitsune's
  `ModelBase`, with `get_parent()`, `get_children()`, `add_child()`, `get_ancestors()`,
  `get_descendants()`, and `get_root()`.
- `GroupProfile` (`kitsune.groups.models`): extends Django's `Group` with the hierarchy.
  Fields: `slug`, `group` (ForeignKey), `leaders`, `information`, `avatar`, `visibility`,
  `isolation_enabled`, `visible_to_groups`. Methods: `can_moderate_group()`, `can_edit()`,
  `can_delete_subgroup()`, `can_view()`, `get_visible_children()`.

## Visibility levels

| Level | Who sees it |
| --- | --- |
| PUBLIC | Everyone, including anonymous users. No isolation. |
| PRIVATE | Members and moderators within the hierarchy. With isolation (the default) they see only their own branch; without it, members see the whole tree. |
| MODERATED | Same as PRIVATE, plus view-only access for the groups in `visible_to_groups`. |

Children always match their parent's visibility (`save()` enforces it), and changing the
root's visibility propagates to all descendants, so a tree never mixes levels.

## Isolation

PRIVATE and MODERATED groups have `isolation_enabled` (default `True`). PUBLIC groups have
no isolation, since they are visible to everyone.

```
Root (members: Alice, Bob; moderator: Mike)
├── SubA (members: Alice, Charlie)
└── SubB (member: Bob)

Mike (root moderator):  Root, SubA, SubB (whole tree, can edit)
Alice (root member):    Root, SubA, SubB (whole tree, view only)
Bob (root member):      Root, SubA, SubB (whole tree, view only)
Charlie (SubA member):  Root, SubA only (sibling isolation hides SubB)
```

- Root moderators view and edit the whole tree; root members view it read-only.
- Members of a subgroup who aren't root members see their ancestors and their own subtree,
  never sibling groups.
- Everyone in a hierarchy can see its ancestor groups.

Isolation prevents leaking that sibling groups exist:

```
Organization (PRIVATE, isolation on)
├── GroupA (members: Alice, Bob)
└── GroupB (members: Charlie, Dana)

Alice and Bob can't discover GroupB; Charlie and Dana can't discover GroupA.
```

## Leadership and moderation

A group's leaders (`leaders`) are its moderators.

- **Root leaders** moderate the whole tree: they add or remove members anywhere, edit any
  group, and are the only ones who can delete subgroups.
- **Other leaders** moderate only their own group (members and settings), not its
  descendants, and can't delete subgroups.
- A group without leaders is moderated by the **root's** leaders, not its parent's, so
  only root leaders or a group's own leaders ever manage it.
- A root must have at least one leader.

```
Root (leader: Mike)
├── SubA (leader: Alice)
│   └── SubSubA (no leader)
│       └── SubSubSubA (no leader)
└── SubB (no leader)

Mike:   moderates and edits every group; can delete any subgroup.
Alice:  moderates and edits SubA only; not SubSubA; can't delete subgroups.
SubSubA and SubSubSubA: moderated by Mike (root), not Alice.
```

## Security

Always query with `GroupProfile.objects.visible(request.user)` or check `can_view()`.
`GroupProfile.objects.all()` bypasses visibility and isolation and exposes PRIVATE groups to
anyone; every view must use one of the safe paths.

## Cross-hierarchy view access

`visible_to_groups` (M2M) gives external groups view-only access to a MODERATED group without
membership, for oversight, auditing, or cross-team visibility. They can't edit or moderate it.

## Testing

`kitsune/groups/tests/test_models.py` covers moderation scope, visibility with and without
isolation, sibling isolation, MODERATED cross-hierarchy access, visible children, leader
visibility, and visibility inheritance. Enterprise tests are listed in
[Enterprise support](enterprise-support.md#testing).

```bash
docker compose run --rm web python manage.py test kitsune.groups.tests
docker compose run --rm web python manage.py test kitsune.groups.tests.test_models
```

## Key behaviors

- **Visibility inheritance**: children match their parent's visibility.
- **Moderation scope**: root leaders manage the whole tree; other leaders only their own
  group.
- **Moderation inheritance**: groups without leaders fall back to the root's, not the
  parent's.
- **Member visibility**: root members see the whole tree; subgroup members see only their
  branch (with isolation).
- **Deletion rights**: only root leaders can delete subgroups.

## References

- [#2692 - Nested Groups](https://github.com/mozilla/sumo/issues/2692)
- [django-treebeard](https://django-treebeard.readthedocs.io/)
- Code: `kitsune/groups/models.py`, `managers.py`, `views.py`; tests in
  `kitsune/groups/tests/test_models.py`
