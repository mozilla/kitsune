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
npm start
```

And run kitsune through the debugger:
```
>Debug: Start Debugging
```

## Running without debugging

To run kitsune without debugging, ensure you start browser-sync and asset rebuilding as before with:
```
npm start
```

And run kitsune with this vscode command instead:
```
>Run: Start Without Debugging
```

## Stopping a stubborn kitsune instance

If you launch the "Kitsune" config in vscode, sometimes the server won't stop when you stop debugging.

In order to stop the server so you can start debugging again run the vscode command:
```
>Remote-Containers: Rebuild Container
```

## Debugging a python script executed through the terminal (e.g. a django management command)

There's a helper script which will wrap any execution of a python script with vscode's debugger.

To use it, run:

```
.vscode/debug-python <script and arguments here>
```

e.g.

```
./vscode/debug-python ./manage.py help
```

The script's execution is paused until the debugger attaches to it.
So to start it,
open the run sidebar in vscode,
select "Attach to .vscode/debug-python" from the dropdown,
and click run.
