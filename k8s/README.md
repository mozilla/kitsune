# SUMO K8s deployment

## Local Requirements:

- Python 3
- Connectivity to SUMO Kubernetes cluster(s)

## Deploying SUMO

#### Setup

- Move to the SUMO `k8s` directory

  ```sh
  cd k8s
  ```

```sh
pip install -r ./requirements.txt
```

- Decide which settings file you'll be using from `./regions/region_name/<env>.yaml`

#### Listing available tasks

```sh
$ invoke -l
Available tasks:

  deployments.check-environment   Ensure that a .yaml file has been specified
  deployments.create-celery       Create or update a SUMO celery deployment
  deployments.create-cron         Create or update a SUMO cron deployment
  deployments.create-nodeport     Create or update a SUMO nodeport
  deployments.create-web          Create or update a SUMO web deployment
  deployments.delete-celery       Delete an existing SUMO celery deployment
  deployments.delete-cron         Delete an existing SUMO cron deployment
  deployments.delete-nodeport     Delete an existing SUMO nodeport
  deployments.delete-web          Delete an existing SUMO web deployment
  rollouts.check-environment      Ensure that a .yaml file has been specified
  rollouts.rollback-celery        Undo a celery deployment
  rollouts.rollback-cron          Undo a cron deployment
  rollouts.rollback-web           Undo a web deployment
  rollouts.status-celery          Check rollout status of a SUMO web deployment
  rollouts.status-cron            Check rollout status of a SUMO web deployment
  rollouts.status-web             Check rollout status of a SUMO web deployment
```

#### Deploying SUMO

- Update the settings file with new image tags and settings.

- If desired, perform a dry-run to see rendered K8s settings:

```sh
invoke -f ./regions/oregon-b/dev.yaml deployments.create-celery
invoke -f ./regions/oregon-b/dev.yaml deployments.create-cron
invoke -f ./regions/oregon-b/dev.yaml deployments.create-web
```

> dry-run mode is enabled if you do not specify `--apply`.

- Apply changes to K8s:

```
invoke -f ./regions/oregon-b/dev.yaml deployments.create-celery --apply
invoke -f ./regions/oregon-b/dev.yaml deployments.create-cron --apply
invoke -f ./regions/oregon-b/dev.yaml deployments.create-web --apply
```

- Monitor the status of the rollout until it completes:

```sh
invoke -f ./regions/oregon-b/dev.yaml rollouts.status-celery
invoke -f ./regions/oregon-b/dev.yaml rollouts.status-cron
invoke -f ./regions/oregon-b/dev.yaml rollouts.status-web
```

- In an emergency, if the rollout is causing failures, you can roll-back to the previous state.

```sh
invoke -f ./regions/oregon-b/dev.yaml rollouts.rollback-celery
invoke -f ./regions/oregon-b/dev.yaml rollouts.rollback-cron
invoke -f ./regions/oregon-b/dev.yaml rollouts.rollback-web
```

----

##### kubectl client version note

When connecting to an older K8s cluster, such as Frankfurt, you may need to download an older version of Kubectl that matches the version of the server.

Newer clients connecting to older K8s servers may display error messages such as:

    Error from server (NotFound): the server could not find the requested resource


To determine the K8s server version:

```sh
$ kubectl version
Client Version: version.Info{Major:"1", Minor:"9", GitVersion:"v1.9.1", GitCommit:"3a1c9449a956b6026f075fa3134ff92f7d55f812", GitTreeState:"clean", BuildDate:"2018-01-04T11:52:23Z", GoVersion:"go1.9.2", Compiler:"gc", Platform:"linux/amd64"}
Server Version: version.Info{Major:"1", Minor:"6", GitVersion:"v1.6.4", GitCommit:"d6f433224538d4f9ca2f7ae19b252e6fcb66a3ae", GitTreeState:"clean", BuildDate:"2017-05-19T18:33:17Z", GoVersion:"go1.7.5", Compiler:"gc", Platform:"linux/amd64"}
```

Check the values that are part of `Server Version`. The output above shows `1.6` (or `v.1.6.4`).

Next, download a binary following the instructions located [here](https://kubernetes.io/docs/tasks/tools/install-kubectl/). 

```sh
curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.6.4/bin/linux/amd64/kubectl
chmod +x ./kubectl
# it may be useful to rename the binary to include K8s version number:
mv ./kubectl ./kubectl1.6.4
```

Next, set the `KUBECTL_BIN` environment variable to override the name of the kubectl binary:

```sh
# next, set the KUBECTL_BIN environment variable to override the name of the kubectl binary:
KUBECTL_BIN=/home/metadave/kubectl1.6.4 invoke -f ./regions/oregon-b/dev.yaml deployments.create-web --apply
```

> the default KUBECTL_BIN value is `kubectl`.
