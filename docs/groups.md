# Groups System

Kitsune's groups system provides hierarchical organization for users with configurable visibility, isolation, and leadership delegation.

## Overview

Groups enable organizing users into hierarchical structures for:
- **Content Access Control**: Restrict wiki articles, questions, and other content to specific groups
- **Moderation Delegation**: Assign leaders who manage group members and content
- **Hierarchical Organization**: Support nested group structures with parent-child relationships
- **Isolated Workspaces**: Prevent sibling groups from discovering each other

## Architecture

### Hierarchy Structure

Groups use django-treebeard's Materialized Path (MP_Node) implementation:
- **Unlimited depth**: Support for deeply nested structures (recommended max: 3-4 levels)
- **Single parent**: Each group belongs to exactly one parent (no multiple inheritance)
- **Efficient queries**: Path-based lookups for ancestors and descendants

**Example Hierarchy:**
```
Organization (root)
├── GroupA
│   ├── SubgroupX
│   └── SubgroupY
└── GroupB
    └── SubgroupZ
```

### Key Models

**TreeModelBase** (`kitsune.groups.models.TreeModelBase`)
- Abstract base combining `MP_Node` (tree operations) + `ModelBase` (Kitsune methods)
- Provides: `get_parent()`, `get_children()`, `add_child()`, `get_ancestors()`, `get_descendants()`, `get_root()`

**GroupProfile** (`kitsune.groups.models.GroupProfile`)
- Profile extending Django's `Group` with hierarchy support
- Fields: `slug`, `group` (ForeignKey), `leaders` (M2M), `information`, `avatar`, `visibility`, `isolation_enabled`, `visible_to_groups`
- Methods: `can_moderate_group()`, `can_edit()`, `can_delete_subgroup()`, `can_view()`, `get_visible_children()`

## Visibility Levels

Groups have three visibility levels that control discovery and access.

### PUBLIC
- **Who can see**: Everyone (anonymous and authenticated users)
- **Isolation**: None - all PUBLIC groups are globally visible
- **Behavior**: No restrictions on visibility

### PRIVATE
- **Who can see**: Depends on `isolation_enabled` setting (default: True)
- **With isolation enabled**: Members/moderators see only their hierarchy (sibling isolation)
- **With isolation disabled**: Members see entire tree
- **Behavior**: Restricts visibility to members and moderators within the hierarchy

### MODERATED
- **Functionality**: Identical to PRIVATE
- **Additional feature**: `visible_to_groups` for cross-hierarchy view access
- **Behavior**: Same as PRIVATE, plus allows specific external groups to view (but not edit)

## Isolation

### Isolation Setting

Both PRIVATE and MODERATED groups have an `isolation_enabled` field (default: `True`). PUBLIC groups do not have isolation as it doesn't make sense for publicly visible content.

**With Isolation Enabled (default):**
```
Root (member: Alice, Bob; moderator: Mike)
├── SubA (member: Alice, Charlie)
└── SubB (member: Bob)

Mike (root moderator):     Sees Root, SubA, SubB (entire tree)
Alice (root member):       Sees Root, SubA, SubB (entire tree, view-only)
Bob (root member):         Sees Root, SubA, SubB (entire tree, view-only)
Charlie (node member):     Sees Root, SubA ONLY (sibling isolation - no SubB)
```

**Key Rules:**
- **Root moderators**: View + edit entire tree
- **Root members**: View entire tree (read-only)
- **Node members** (not root members): View ancestors + own subtree (sibling isolation)
- **Ancestors always visible**: Everyone in a hierarchy can see ancestor groups

### Why Isolation Matters

Sibling isolation prevents cross-group information leakage:
```
Organization (PRIVATE, isolation=True)
├── GroupA (members: Alice, Bob)
└── GroupB (members: Charlie, Dana)

- Alice and Bob cannot discover GroupB exists
- Charlie and Dana cannot discover GroupA exists
- Prevents users from discovering sibling groups they are not members of
```

## Leadership and Moderation

### Moderation Hierarchy

**Root Moderators (full tree access):**
- Leaders of root group can moderate entire tree
- Can add/remove members anywhere
- Can edit all group settings
- **Only ones who can delete subgroups**

**Non-Root Moderators (limited to their group):**
- Can moderate ONLY their specific group (not descendants)
- Can add/remove members to their group
- Can edit their group's settings
- **Cannot delete subgroups**

**Example:**
```
Root (moderator: Mike)
├── SubA (moderator: Alice)
│   └── SubSubA (no moderator)
└── SubB (no moderator)

Mike can:
- Moderate Root, SubA, SubSubA, SubB
- Edit all groups
- Delete any subgroup

Alice can:
- Moderate SubA ONLY
- Edit SubA ONLY
- NOT manage SubSubA (her descendant)
- NOT delete subgroups
```

### Moderation Inheritance

If a group has no assigned moderators, moderation **inherits from ROOT only** (not parent):

```
Root (moderator: Mike)
└── SubA (moderator: Alice)
    └── SubSubA (no moderator)
        └── SubSubSubA (no moderator)

SubSubA: Moderated by Mike (root), NOT Alice (parent)
SubSubSubA: Moderated by Mike (root), NOT Alice (grandparent)
```

**Why skip parent?** This ensures clear chain of command - only root moderators or explicitly assigned group moderators can manage groups.

### Root Must Have Moderators

**Validation**: Root groups must have at least one moderator assigned. This ensures there's always someone who can manage the entire tree.

## Visibility Inheritance

**Strict Inheritance Rule**: Children automatically inherit parent's visibility.

- Cannot mix visibility levels in a tree (e.g., PUBLIC parent with PRIVATE child)
- Enforced by `save()` method - children automatically match parent's visibility
- Changing root visibility propagates to all descendants

## Security

### Critical: Always Use `.visible()`

**⚠️ SECURITY WARNING**: Always use `GroupProfile.objects.visible(user)` instead of `.all()` when querying groups. Using `.all()` bypasses visibility and isolation rules, potentially exposing PRIVATE groups to unauthorized users.

- ✅ **SECURE**: `GroupProfile.objects.visible(request.user)` - Respects visibility and isolation
- ❌ **INSECURE**: `GroupProfile.objects.all()` - Bypasses all security, exposes all groups

All views must filter by `.visible()` or explicitly check `can_view()` permissions.

## Cross-Hierarchy View Access

The `visible_to_groups` M2M field allows external groups to have **view-only** access to MODERATED groups. This enables oversight or auditing scenarios where certain groups need to see (but not edit) other groups outside their hierarchy.

**Behavior:**
- External groups can view MODERATED groups without being members
- View-only access (cannot edit or moderate)
- Useful for oversight, auditing, or cross-team visibility

## Testing

Test coverage includes 58 tests in `kitsune/groups/tests/test_models.py`:
- **ModerationHierarchyTests**: Root vs non-root moderator permissions (6 tests)
- **VisibilityWithIsolationTests**: Visibility rules with isolation enabled (4 tests)
- **PublicGroupsNoIsolationTests**: PUBLIC group behavior (2 tests)
- **ModeratedGroupsTests**: MODERATED group behavior and cross-hierarchy access (2 tests)
- **IsolationDisabledTests**: Behavior when isolation is disabled (1 test)
- **SiblingIsolationTests**: Sibling isolation functionality (7 tests)
- **VisibilityEdgeCaseTests**: Edge cases in group visibility (9 tests)
- **GetVisibleChildrenTests**: Visible children filtering (5 tests)
- **LeadershipVisibilityTests**: Leader visibility permissions (6 tests)
- **VisibilityInheritanceTests**: Visibility inheritance rules (2 tests)
- **ModeratedVisibilityTests**: MODERATED group visibility (5 tests)

Run tests:
```bash
# All groups tests
python manage.py test kitsune.groups.tests

# Specific test file
python manage.py test kitsune.groups.tests.test_models
```

## Key Behaviors

- **Visibility Inheritance**: Children automatically match parent's visibility level
- **Moderation Scope**: Root moderators manage entire tree; non-root moderators manage only their specific group
- **Moderation Inheritance**: Groups without assigned moderators inherit from root (not parent)
- **Member Visibility**: Root members see entire tree; node members see only their subtree (with sibling isolation)
- **Deletion Rights**: Only root moderators can delete subgroups

## References

- **GitHub Issue**: [#2692 - Nested Groups](https://github.com/mozilla/sumo/issues/2692)
- **django-treebeard**: https://django-treebeard.readthedocs.io/
- **Model**: `kitsune/groups/models.py`
- **Manager**: `kitsune/groups/managers.py`
- **Views**: `kitsune/groups/views.py`
- **Tests**: `kitsune/groups/tests/test_models.py`
