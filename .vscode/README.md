# Development in vscode (beta)

Install [vscode](https://code.visualstudio.com/) and the [Remote Development](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.vscode-remote-extensionpack) extension.

Launch vscode wherever you cloned this repo:
```
code .
```

In the vscode command palette (Ctrl+Shift+P) build and launch the container:
```
>Remote-Containers: Rebuild and Reopen in Container
```

Once vscode has reopened in the container, open a terminal (View > Terminal) and start browser-sync and the on-demand asset rebuilding:
```
npm run start-in-container
```

And run kitsune through the debugger:
```
>Debug: Start Debugging
```
