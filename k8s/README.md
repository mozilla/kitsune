# SUMO K8s deployment

## Local Requirements:

- Python 3
- Connectivity to SUMO Kubernetes cluster(s)

## Release convention

* Releases to the development environment can happen either from the master or from a feature branch.
* Releases to the stage environment happen from the master branch.
* Releases to the production environment happen from the master branch after successful QA testing in the stage environment.

```
Because there might be need to deploy while testing merged changes in master,
deployments to production and stage may happen from the production branch.
The production branch maintains an image that can be released in production without further validation.
```

## Deploying SUMO

#### Setup

- Move to the SUMO `k8s` directory

  ```sh
  cd k8s
  ```

- Install needed packages

  ```sh
  virtualenv venv
  pip install -r ./requirements.txt
  ```

- Create symbolic links to `kubectl` and `kubeconfig` to use in each region

  e.g. `ln -s ~/bin/kubectl ./regions/frankfurt/kubectl`

  Files to be created:
    - ./regions/frankfurt/kubectl
    - ./regions/frankfurt/kubeconfig
    - ./regions/oregon-a/kubectl
    - ./regions/oregon-a/kubeconfig
    - ./regions/oregon-b/kubectl
    - ./regions/oregon-b/kubeconfig

- Create symbolic links to secrets for each namespace and region.

  e.g. `ln -s ~/sumo-encrypted/k8s/secrets/frankfurt/sumo-dev-secrets.yaml ./regions/frankfurt/dev-secrets.yaml`

  Files to be created:
    - ./regions/frankfurt/dev-secrets.yaml
    - ./regions/frankfurt/stage-secrets.yaml
    - ./regions/frankfurt/prod-secrets.yaml
    - ./regions/oregon-a/stage-secrets.yaml
    - ./regions/oregon-a/prod-secrets.yaml
    - ./regions/oregon-b/stage-secrets.yaml
    - ./regions/oregon-b/prod-secrets.yaml


#### Deploy SUMO with commander (recommended)

Choose a region and env:

| Region  | Env  |
|---|---|
| frankfurt  | dev  |
| frankfurt  | stage |
| frankfurt  | prod |
| oregon-a  | stage |
| oregon-a  | prod |
| oregon-b  | stage |
| oregon-b  | prod |


- Update the settings file with new image tags and settings.

- Deploy with commander *without secrets*

  `./commander.sh deploy <region> <environment> <git sha>`

  E.g. `./commander.sh deploy frankfurt dev d7be392`

- Deploy with commander *with secrets*

  `./commander.sh deploy <region> <environment> <git sha> secrets`

  E.g. `./commander.sh deploy frankfurt dev d7be392 secrets`


#### Deploying SUMO (low level)

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

#### Acceptance Tests

Run basic acceptance tests with

  `./acceptance-tests.sh <URL>`

  E.g. `./acceptance-tests.sh https://dev.sumo.mozit.cloud`


#### List of invoke available tasks

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

----

##### kubectl client version note

>All Kubernetes clusters that serve SUMO are currently v1.10.xx

When connecting to an older K8s cluster, you may need to download an older version of Kubectl that matches the version of the server.

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

## Checking the Celery queue

In order to check the size of an instance's celery queue, open a shell on a pod in that namespace:

```
kubectl exec -ti sumo-dev-celery-abc -- /bin/bash
```

Get the name of the queue you want to query:

```
./manage.py celery inspect active_queues
```

Open a python shell:

```
./manage.py shell_plus
```

Get the url of the redis instance:
```
In [1]: settings.BROKER_URL
Out[1]: 'redis://hostname:port/db'
```

Set up the redis client:
```
import redis
r = redis.Redis(host='hostname', port='port', db=db)
```

Then query the length of the queue, in this case called 'celery':
```
In [4]: r.llen('celery')
Out[4]: 44
```

The last item in the queue can be fetched with:
```
l = r.lrange('celery', -1, -1)
```

This must then be parsed and de-pickled:
```
import pickle, base64, json
pickle.loads(base64.decodestring(json.loads(l[0])['body']))
```
