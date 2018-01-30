# SUMO K8s deployment

## Local Requirements:

- Python 3
- Connectivity to SUMO Kubernetes cluster(s)

## Deploying SUMO

#### Setup

- Move to the SUMO `k8s` directory

  ```sh
  cd infra/apps/sumo/k8s
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
  deployments.create-nodeport     Create or update a SUMO nodeport
  deployments.create-web          Create or update a SUMO web deployment
  deployments.delete-nodeport     Delete an existing SUMO nodeport
  deployments.delete-web          Delete an existing SUMO web deployment
  rollouts.check-environment      Ensure that a .yaml file has been specified
  rollouts.rollback-web           Undo a deployment
  rollouts.status-web             Check rollout status of a SUMO web deployment
```

#### Deploying SUMO

- Update the settings file with new image tags and settings.

- If desired, perform a dry-run to see rendered K8s settings:

```sh
invoke -f ./regions/oregon-b/dev.yaml deployments.create-web
```

- Apply changes to K8s:

```
invoke -f ./regions/oregon-b/dev.yaml deployments.create-web --apply
```

- Monitor the status of the rollout until it completes:

```sh
invoke -f ./regions/oregon-b/dev.yaml rollouts.status-web
```

- In an emergency, if the rollout is causing failures, you can roll-back to the previous state.

```sh
invoke -f ./regions/oregon-b/dev.yaml rollouts.rollback-web:
```

