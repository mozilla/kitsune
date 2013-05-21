DELETE FROM auth_group_permissions
    WHERE permission_id IN (SELECT id FROM auth_permission WHERE codename LIKE 'delete_document_%');

DELETE FROM auth_user_user_permissions
    WHERE permission_id IN (SELECT id FROM auth_permission WHERE codename LIKE 'delete_document_%');

DELETE FROM auth_permission WHERE codename LIKE 'delete_document_%';
