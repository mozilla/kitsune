# Elevated Browser Permissions

support.mozilla.org has certain elevated permissions in Firefox,
shown in [the Firefox source code](https://searchfox.org/mozilla-central/source/browser/app/permissions),
allowing it to control various aspects of Firefox's UI and retrieve debugging information.

Testing this on our [other deployments](deployments) or locally requires extra configuration and setup.

## Adding permissions

There's a couple of ways to add permissions,
one which happens instantly but doesn't survive browser restarts,
and the other which requires a restart to enable but also persists across restarts:

### Temporarily

This method requires us to execute an expression in the Browser Console,
so we need to enable [the Browser Console command line](https://developer.mozilla.org/en-US/docs/Tools/Browser_Console#Browser_Console_command_line).

Once that's enabled,
follow [the instructions on how to open the Browser Console](https://developer.mozilla.org/en-US/docs/Tools/Browser_Console#Opening_the_Browser_Console),
then run the following command,
substituting `<origin>` and `<permission>` where relevant based on the instructions in the following sections:

```
Services.perms.addFromPrincipal(
  Services.scriptSecurityManager.createContentPrincipalFromOrigin("<origin>"),
  "<permission>",
  Services.perms.ALLOW_ACTION
);
```

Reload the tab containing the page which is attempting to use these elevated permissions and it should have them.

### Permanently

Permissions granted with the above method are cleared once the browser restarts.
To enable them permanently then a slightly different approach must be taken.

First copy the contents of [`resource://app/defaults/permissions`](https://searchfox.org/mozilla-central/source/browser/app/permissions) to a local file.

Then in `about:config` change the `permissions.manager.defaultsUrl` preference to the path of the file you just created,
for example `file:///path_to_your_kitsune_dir/permissions`.

Now add a line enabling the relevant `<permission>` for the relevant `<origin>`:

```
origin	<permission>	1	<origin>
```

Finally restart Firefox to pick up these changes.
Any time you want to change the permissions an origin has you'll also need to restart Firefox.

## Testing locally

Firefox only grants permissions to `https` origins,
so we need to serve our local instance over `https`.
The easiest way to do this is to set up a reverse proxy,
with a tool like [`local-ssl-proxy`](https://github.com/cameronhunter/local-ssl-proxy):

```
npm install -g local-ssl-proxy
```

Then run the proxy:

```
local-ssl-proxy -n 127.0.0.1 --source 8001 --target 8000
```

And access Kitsune at `https://127.0.0.1:8001`,
which will also be your `<origin>`.

## Remote Troubleshooting (about:support) API

The remote troubleshooting API allows support.mozilla.org to access the contents of the `about:support` page.

An additional permission needs to be granted to any origin you want to test this API on.
Open `about:config` and append the relevant `<origin>` to the `webchannel.allowObject.urlWhitelist` preference.

Then [grant the permission](#adding-permissions) as above,
where `<permission>` is `remote-troubleshooting`.

### Examples

To enable permanently on staging:

1. Add `https://support.allizom.org` to `webchannel.allowObject.urlWhitelist`.

2. Add `origin	remote-troubleshooting	1	https://support.allizom.org` to your [permissions file](#permanently).

3. Restart Firefox.

## UITour API

The [UITour API](https://firefox-source-docs.mozilla.org/browser/components/uitour/docs/UITour-lib.html) allows support.mozilla.org to control various aspects of the Firefox UI.

It can be enabled by [granting the permission](#adding-permissions) as above,
where `<permission>` is `uitour`.

However a far simpler way to enable it is to set a couple of custom preferences in `about:config` as explained in [the Bedrock docs](https://bedrock.readthedocs.io/en/latest/uitour.html#local-development).
