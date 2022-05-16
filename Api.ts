import {OCSResult} from "NC";
import Thenable = JQuery.Thenable;
import {FolderGroupsProps} from "./FolderGroups";

export interface Group {
	id: string;
	displayname: string;
}

export interface OCSUser {
	uid: string;
	displayname: string;
}

export interface OCSGroup {
	gid: string;
	displayname: string;
}

export interface ManageRuleProps {
	type: string;
	id: string;
	displayname: string;
}


export interface Folder {
	id: number;
	mount_point: string;
	quota: number;
	size: number;
	groups: { [group: string]: number };
	acl: boolean;
	manage: ManageRuleProps[];
}

export class Api {
	getUrl(endpoint: string): string {
		return OC.generateUrl(`apps/groupfolders/${endpoint}`);
	}

	listFolders(): Thenable<Folder[]> {
		return $.getJSON(this.getUrl('folders'))
			.then((data: OCSResult<Folder[]>) => Object.keys(data.ocs.data).map(id => data.ocs.data[id]));
	}

	listGroups(): Thenable<Group[]> {
		return $.getJSON(this.getUrl('delegation/groups'))
			.then((data: OCSResult<Group[]>) => data.ocs.data);
	}

	createFolder(mountPoint: string): Thenable<number> {
		return $.post(this.getUrl('folders'), {
			mountpoint: mountPoint
		}, null, 'json').then((data: OCSResult<{ id: number; }>) => data.ocs.data.id);
	}

	deleteFolder(id: number): Thenable<void> {
		return $.ajax({
			url: this.getUrl(`folders/${id}`),
			type: 'DELETE'
		});
	}

	addGroup(folderId: number, group: string): Thenable<void> {
		return $.post(this.getUrl(`folders/${folderId}/groups`), {
			group
		});
	}

	removeGroup(folderId: number, group: string): Thenable<void> {
		return $.ajax({
			url: this.getUrl(`folders/${folderId}/groups/${group}`),
			type: 'DELETE'
		});
	}

	setPermissions(folderId: number, group: string, permissions: number): Thenable<void> {
		return $.post(this.getUrl(`folders/${folderId}/groups/${group}`), {
			permissions
		});
	}

	setManageACL(folderId: number, type: string, id: string, manageACL: boolean): Thenable<void> {
		return $.post(this.getUrl(`folders/${folderId}/manageACL`), {
			mappingType: type,
			mappingId: id,
			manageAcl: manageACL ? 1 : 0
		});
	}

	setQuota(folderId: number, quota: number): Thenable<void> {
		return $.post(this.getUrl(`folders/${folderId}/quota`), {
			quota
		});
	}

	setACL(folderId: number, acl: boolean): Thenable<void> {
		return $.post(this.getUrl(`folders/${folderId}/acl`), {
			acl: acl ? 1 : 0
		});
	}

	renameFolder(folderId: number, mountpoint: string): Thenable<void> {
		return $.post(this.getUrl(`folders/${folderId}/mountpoint`), {
			mountpoint
		});
	}

	aclMappingSearch(folderId: number, search: string): Thenable<{groups: OCSGroup[], users: OCSUser[]}> {
		return $.getJSON(this.getUrl(`folders/${folderId}/search?format=json&search=${search}`))
			.then((data: OCSResult<{ groups: OCSGroup[]; users: OCSUser[]; }>) => {
				return {
					groups: Object.values(data.ocs.data.groups).map((item) => {
						return {
							type: 'group',
							id: item.gid,
							displayname: item.displayname
						}
					}),
					users: Object.values(data.ocs.data.users).map((item) => {
						return {
							type: 'user',
							id: item.uid,
							displayname: item.displayname
						}
					})
				}
			});
	}
}
