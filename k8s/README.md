# SUMO K8s deployment

## Local Requirements:

-   Python 3
-   Connectivity to SUMO Kubernetes cluster(s)

## Release convention

-   Releases to the development environment can happen either from the main or from a feature branch.
-   Releases to the stage environment happen from the main branch.
-   Releases to the production environment happen from the main branch after successful QA testing in the stage environment.

```
Because there might be a need to deploy while testing merged changes in main,
deployments to production and stage may happen from the production branch.
The production branch maintains an image that can be released in production without further validation.
```

## Deploying SUMO

### Setup

-   Move to the SUMO `k8s` directory

    ```sh
    cd k8s
    ```

-   Install needed packages

    ```sh
    virtualenv venv
    pip install -r ./requirements.txt
    ```

-   Create symbolic links to secrets for each namespace and region.

    e.g. `ln -s ~/sumo-encrypted/k8s/secrets/frankfurt/sumo-stage-secrets.yaml ./regions/frankfurt/stage-secrets.yaml`

    Files to be created:

    -   ./regions/frankfurt/stage-secrets.yaml
    -   ./regions/frankfurt/prod-secrets.yaml
    -   ./regions/oregon/stage-secrets.yaml
    -   ./regions/oregon/prod-secrets.yaml

-   (Optional) Create symbolic links to `kubectl` and `kubeconfig` to use in each region. Note that `kubectl` should match the version of the cluster, or have a version skew of 1 minor version.

    e.g. `ln -s ~/bin/kubectl ./regions/frankfurt/kubectl`

    Files to be created:

    -   ./regions/frankfurt/kubectl
    -   ./regions/frankfurt/kubeconfig
    -   ./regions/oregon/kubectl
    -   ./regions/oregon/kubeconfig

#### Configuration for deploying into an EKS cluster

-   Ensure that your `kubectl` binary matches the cluster version (check the cluster version in the table below).

-   Authorize yourself into AWS. After making sure you are part of the right LDAP groups, run `$(maws)` to get a short lived AWS token. More on installing maws [here](https://mana.mozilla.org/wiki/display/SECURITY/How+to+login+to+AWS+with+Single+Sign+On).

- Get the `kubeconfig` file running `aws eks update-kubeconfig --name <cluster_name> --region <region> --alias <cluster_name>` adding the cluster name and region. You can find a table with the EKS clusters and regions below.
This command will by default append the configuration to `~/.kube/config`. After that, you should be able to talk to the cluster and perform operations like `kubectl get namespaces`.

Here there is a list with the names of the clusters per region:
| Region | Cluster Name | Version |
|---|---|---|
| eu-central-1 | sumo-eks-eu-central-1 | 1.21 |
| us-west-2 | sumo-eks-us-west-2 | 1.21 |

#### Deploy SUMO with commander (recommended)

Choose a region and env:

| Region  | Env  | Namespace | Cluster | Version |
|---|---|---|---|
| frankfurt | stage | sumo-stage | eks | 1.21 |
| frankfurt | prod  | sumo-prod | eks | 1.21 |
| oregon    | stage | sumo-stage | eks | 1.21 |
| oregon    | prod  | sumo-prod | eks | 1.21 |

-   Update the settings file with new image tags and settings.

-   Update the settings file with new image tags and settings.

-   Deploy with commander _without secrets_

    `./commander.sh deploy <region> <environment> <git sha>`

    E.g. `./commander.sh deploy frankfurt dev d7be392`

-   Deploy with commander _with secrets_

    `./commander.sh deploy <region> <environment> <git sha> secrets`

    E.g. `./commander.sh deploy frankfurt dev d7be392 secrets`

#### Deploying SUMO (low level)

-   Update the settings file with new image tags and settings.

-   If desired, perform a dry-run to see rendered K8s settings:

```sh
invoke -f ./regions/frankfurt/dev.yaml deployments.create-celery
invoke -f ./regions/frankfurt/dev.yaml deployments.create-cron
invoke -f ./regions/frankfurt/dev.yaml deployments.create-web
```

> dry-run mode is enabled if you do not specify `--apply`.

-   Apply changes to K8s:

```
invoke -f ./regions/frankfurt/dev.yaml deployments.create-celery --apply
invoke -f ./regions/frankfurt/dev.yaml deployments.create-cron --apply
invoke -f ./regions/frankfurt/dev.yaml deployments.create-web --apply
```

-   Monitor the status of the rollout until it completes:

```sh
invoke -f ./regions/frankfurt/dev.yaml rollouts.status-celery
invoke -f ./regions/frankfurt/dev.yaml rollouts.status-cron
invoke -f ./regions/frankfurt/dev.yaml rollouts.status-web
```

-   In an emergency, if the rollout is causing failures, you can roll-back to the previous state.

```sh
invoke -f ./regions/frankfurt/dev.yaml rollouts.rollback-celery
invoke -f ./regions/frankfurt/dev.yaml rollouts.rollback-cron
invoke -f ./regions/frankfurt/dev.yaml rollouts.rollback-web
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
  deployments.create-all          Create web, cron and celery deployments
  deployments.create-celery       Create or update a SUMO celery deployment
  deployments.create-cron         Create or update a SUMO cron deployment
  deployments.create-service      Create or update a SUMO service with ELB
  deployments.create-web          Create or update a SUMO web deployment
  deployments.delete-all          Delete existing web, cron and celery deployments
  deployments.delete-celery       Delete an existing SUMO celery deployment
  deployments.delete-cron         Delete an existing SUMO cron deployment
  deployments.delete-service      Delete an existing SUMO service ELB
  deployments.delete-web          Delete an existing SUMO web deployment
  rollouts.check-environment      Ensure that a .yaml file has been specified
  rollouts.rollback-celery        Undo a celery deployment
  rollouts.rollback-cron          Undo a cron deployment
  rollouts.rollback-web           Undo a web deployment
  rollouts.status-celery          Check rollout status of a SUMO web deployment
  rollouts.status-cron            Check rollout status of a SUMO web deployment
  rollouts.status-web             Check rollout status of a SUMO web deployment
```

---

##### kubectl client version note

> All Kubernetes clusters that serve SUMO are currently deployed on EKS version 1.21.2

When connecting to an older K8s cluster, you may need to download an older version of Kubectl that matches the version of the server.

Newer clients connecting to older K8s servers may display error messages such as:

    Error from server (NotFound): the server could not find the requested resource

To determine the K8s server version:

```sh
$ kubectl version --short
Client Version: v1.21.5
Server Version: v1.21.2-eks-06eac09
```

Check the values that are part of `Server Version`. The output above shows `1.21` (or `v.1.21.2-eks-...`).

Next, download a binary following the instructions located [here](https://kubernetes.io/docs/tasks/tools/install-kubectl/).

```sh
curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.21.5/bin/linux/$(uname -m)/kubectl
chmod +x ./kubectl
# it may be useful to rename the binary to include K8s version number:
mv ./kubectl ./kubectl1.21.5
```

Next, set the `KUBECTL_BIN` environment variable to override the name of the kubectl binary:

```sh
# next, set the KUBECTL_BIN environment variable to override the name of the kubectl binary:
KUBECTL_BIN=/home/metadave/kubectl1.21.5 invoke -f ./regions/frankfurt/dev.yaml deployments.create-web --apply
```

> The default KUBECTL_BIN value is `kubectl`.

## Checking the Celery queue

<!-- TODO: update this section once we've upgraded Python/Django to reflect new commands -->

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

# SUMO local development in Kubernetes

## Setting up a local Kubernetes cluster:

This was tested with K3d. Other local Kubernetes clusters should work in a similar way.

To bring up a HA k3d cluster:

```sh

> k3d cluster create sumo-dev-cluster --port "8080:80@loadbalancer" --servers 3 --agents 3 -v path_to_your_project_git_repo:/kitsune --registry-create
```

Get the [kubeconfig](https://k3d.io/usage/kubeconfig/) for the newly created cluster.

Copy the values for the local deployment.

```sh
> cp path_to_your_git_kitsune_repo/k8s/sumo/values.local.yaml-dist path_to_your_git_kitsune_repo/k8s/sumo/values.local.yaml
```

Finally deploy the application

```sh
> cd path_to_your_git_kitsune_repo/k8s/sumo

> helm install -n sumo-local-dev --create-namespace kitsune  -f values.yaml -f values.local.yaml .
```
