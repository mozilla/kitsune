# To get Kitsune running locally all you really need is to have Docker and Docker Compose installed, and follow the following steps.

## Fork this repository & clone it to your local machine.

🚀 git clone https://github.com/mozilla/kitsune.git

## Pull base Kitsune Docker images, run collectstatic, create your database, and install node packages.

🚀 make init <br />
🚀 make build

## If you have low bandwidth, you may get a timeout error, see issue#4511 for more information. You can change default pip’s timeout value (which is 60 seconds) by running:

🚀 make build PIP_TIMEOUT=300

 In above command, we are setting default value of PIP_DEFAULT_TIMEOUT to 5 minutes, change it according to your need.

# Run Kitsune.

🚀 make run

## This will produce a lot of output (mostly warnings at present). When you see the following the server will be ready:

🚀 web_1              | Starting development server at http://0.0.0.0:8000/ <br />
🚀 web_1              | Quit the server with CONTROL-C.

The running instance will be located at http://localhost:8000/ unless you specified otherwise, and the administrative control panel will be at http://localhost:8000/admin/.

# Another way you might choose to run the app (step 3 above) is by getting a shell in the container and then manually running the Django dev server from there. This should make frequent restarts of the server a lot faster and easier if you need to do that:

🚀 make runshell <br />
🚀 bin/run-dev.sh

## The end result of this method should be the same as using make run, but will potentially aid in debugging and act much more like developing without Docker as you may be used to. You should use make runshell here instead of make shell as the latter does not bind port 8000 which you need to be able to load the site.

## Run make help to see other helpful commands.

## Finally you can run the development server with instance reloading through browser-sync.

🚀 npm start

The running instance in this case will be located at http://localhost:3000/.
