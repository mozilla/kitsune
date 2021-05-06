# SUMO Kubernetes Support Guide

## Links

High level:

- [SUMO Infra home](https://github.com/mozilla-it/sumo-infra)
- [Deploying SUMO](https://github.com/mozilla/kitsune/tree/master/k8s#deploying-sumo)
- [MozMEAO escalation path](https://mana.mozilla.org/wiki/pages/viewpage.action?pageId=50267455)

- [Architecture diagram](https://raw.githubusercontent.com/mozilla/kitsune/master/docs/SUMO%20architecture%202019.svg)
    - [Source](https://www.lucidchart.com/documents/view/3687b2eb-57c7-4488-a8b5-4ddcf54e47b3)
- [SLA](https://docs.google.com/document/d/1SYtkEioKl6uvdZZA06YtVigWYJY0Nb9hGfvE0UwEPXA/edit)
- [Incident Reports](https://mana.mozilla.org/wiki/pages/viewpage.action?pageId=52265112)

Tech details:

- [SUMO K8s deployments/services/secrets templates](https://github.com/mozilla/kitsune/tree/master/k8s/)
- [SUMO AWS resource definitions](https://github.com/mozilla-it/sumo-infra/tree/master/k8s/tf)



## K8s commands

> Most of the examples use `sumo-prod` as an example namespace. SUMO dev/stage/prod run in the `sumo-dev`/`sumo-stage`/`sumo-prod` namespaces respectively.

### General

Most examples are using the `kubectl get ...` subcommand. If you'd prefer output that's more readable, you can substitute the `get` subcommand with `describe`:

```
kubectl -n sumo-prod describe pod sumo-prod-web-76b74db69-dvxbh
```

> Listing resources is easier with the `get` subcommand.

To see all SUMO pods currently running:

```
kubectl -n sumo-prod get pods
```

To see all pods running and the K8s nodes they are assigned to:

```
kubectl -n sumo-prod get pods -o wide
```

To show yaml for a single pod:

```
kubectl -n sumo-prod get pod sumo-prod-web-76b74db69-dvxbh -o yaml
```

To show all deployments:

```
 kubectl -n sumo-prod get deployments

NAME               DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
sumo-prod-celery   3         3         3            3           330d
sumo-prod-cron     0         0         0            0           330d
sumo-prod-web      50        50        50           50          331d
```

To show yaml for a single deployment:

```
 kubectl -n sumo-prod get deployment sumo-prod-web -o yaml
```

Run a bash shell on a SUMO pod:

```
kubectl -n sumo-prod exec -it sumo-prod-web-76b74db69-xbfgj bash
```

Scaling a deployment:

```
kubectl -n sumo-prod scale --replicas=60 deployment/sumo-prod-web
```

Check rolling update status:

```
kubectl -n sumo-prod rollout status deployment/sumo-prod-web
```

#### Working with K8s command output

Filtering pods based on a label:

```
kubectl -n sumo-prod -l type=web get pods
```

Getting a list of pods:

```
kubectl -n sumo-prod -l type=web get pods | tail -n +2 | cut -d" " -f 1
```

Structured output:

See the jsonpath guide [here](https://kubernetes.io/docs/reference/kubectl/jsonpath/)

```
kubectl -n sumo-prod get pods -o=jsonpath='{.items[0].metadata.name}'
```

Processing K8s command json output with jq:

> jsonpath may be more portable

```
kubectl -n sumo-prod get pods -o json | jq -r .items[].metadata.name
```


### K8s Services

List SUMO services:

```
kubectl -n sumo-prod get services
NAME            TYPE       CLUSTER-IP      EXTERNAL-IP   PORT(S)         AGE
sumo-nodeport   NodePort   100.71.222.28   <none>        443:30139/TCP   341d
```



### Secrets

[K8s secrets docs](https://kubernetes.io/docs/concepts/configuration/secret/)

Secret values are base64 encoded when viewed in K8s output. Once setup as an environment variable or mounted file in a pod, the values are base64 decoded automatically.

Kitsune uses secrets specified as environment variables in a deployment spec:

- [example](https://github.com/mozilla/kitsune/blob/7ff9934d185ce58153c652928298b5f62d37f8d2/k8s/templates/sumo-app.yaml.j2#L43-L46)

To list secrets:

```
kubectl -n sumo-prod get secrets
```

To view a secret w/ base64-encoded values:

```
kubectl -n sumo-prod get secret sumo-secrets-prod -o yaml
```

To view a secret with decoded values (aka "human readable"):

> This example uses the [ksv](https://github.com/metadave/ksv) utility

```
kubectl -n sumo-prod get secret sumo-secrets-prod -o yaml | ksv
```

To encode a secret value:

```
echo -n "somevalue" | base64
```

> The `-n` flag strips the newline before base64 encoding.
> Values must be specified without newlines, the `base64` command on Linux can take a `-w 0` parameter that outputs without newlines. The `base64` command in Macos Sierra seems to output encoded values without newlines.

Updating secrets:

```
kubectl -n sumo-prod apply -f ./some-secret.yaml
```



## Monitoring

### New Relic		

- [Primary region, A + B "rollup view"](https://rpm.newrelic.com/accounts/1299394/applications/55558271)
    - `sumo-prod-oregon`

- [Primary cluster A](https://rpm.newrelic.com/accounts/1299394/applications/45098028)
    - `sumo-prod-oregon-a`
- [Primary cluster B](https://rpm.newrelic.com/accounts/1299394/applications/45097089)
    - `sumo-prod-oregon-b`
			
- [Failover region](https://rpm.newrelic.com/accounts/1299394/applications/45103938)
    - `sumo-prod-frankfurt`

### Papertrail

All pod output is logged to Papertrail.
- [Oregon-a](https://papertrailapp.com/groups/8137172/events)
- [Oregon-b](https://papertrailapp.com/groups/6778452/events)
    - combined Oregon-A | Oregon-B output can be viewed in the `All Systems` log destination with custom filters.
- [Frankfurt](https://papertrailapp.com/groups/5458941/events)
			
### elastic.co

Our hosted Elasticsearch cluster is in the `us-west-2` region of AWS. Elastic.co hosting status can be found on [this](https://cloud-status.elastic.co/) page.


## Operations

### Cronjobs

The `sumo-prod-cron` deployment is a self-contained Python cron system that ***runs in only one of the primary clusters***. 

```
 # Oregon-A
kubectl -n sumo-prod get deployments
NAME               DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
sumo-prod-celery   3         3         3            3           330d
sumo-prod-cron     1         1         1            1           330d
sumo-prod-web      25        25        25           25          331d

# Oregon-B
kubectl -n sumo-prod get deployments
NAME               DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
sumo-prod-celery   3         3         3            3           330d
sumo-prod-cron     0         0         0            0           330d
sumo-prod-web      50        50        50           50          331d
```


### Manually adding/removing K8s Oregon-A/B/Frankfurt cluster nodes

> If you are modifying the Frankfurt cluster, replace instances of `oregon-*` below with `frankfurt`.

1. login to the AWS console
2. ensure you are in the `Oregon` region
3. search for and select the `EC2` service in the AWS console
4. select `Auto Scaling Groups` from the navigation on the left side of the page
5. click on the `nodes.k8s.us-west-2a.sumo.mozit.cloud` or `nodes.k8s.us-west-2b.sumo.mozit.cloud` row to select it
6. from the `Actions` menu (close to the top of the page), click `Edit`
7. the `Details` tab for the ASG should appear, set the appropriate `Min`, `Desired` and `Max` values.
    1. it's probably good to set `Min` and `Desired` to the same value in case the cluster autoscaler decides to scale down the cluster smaller than the `Min`.
8. click `Save`
9. if you click on `Instances` from the navigation on the left side of the page, you can see the new instances that are starting/stopping.
10. you can see when the nodes join the K8s cluster with the following command:

```
watch 'kubectl get nodes | tail -n +2 | grep -v master | wc -l'
```

> The number that is displayed should eventually match your ASG `Desired` value. Note this value only includes K8s workers.

### Manually Blocking an IP address

1. login to the AWS console
2. ensure you are in the `Oregon` region
3. search for and select the `VPC` service in the AWS console
4. select `Network ACLs` from the navigation on the left side of the page
5. select the row containing the `Oregon-a and b` VPC
6. click on the `Inbound Rules` tab
7. click `Edit`
8. click `Add another rule`
9. for `Rule#`, select a value < 100 and > 0
10. for `Type`, select `All Traffic`
11. for `Source`, enter the IP address in CIDR format. To block a single IP, append `/32` to the IP address.
    1. example: `196.52.2.54/32`    
12. for `Allow / Deny`, select `DENY`
13. click `Save`

There are limits that apply to using VPC ACLs documented [here](http://docs.aws.amazon.com/AmazonVPC/latest/UserGuide/VPC_Appendix_Limits.html#vpc-limits-nacls).


### Manually Initiating Cluster failover

> Note: Route 53 will provide automated cluster failover, these docs cover things to consider if there is a catastrophic failure in Oregon-A and B and Frankfurt must be promoted to primary rather than a read-only failover.

- **verify the Frankfurt read replica**
    - `eu-central-1` (Frankfurt) has a read-replica of the SUMO production database
    - the replica is currently a `db.m4.xlarge`, while the prod DB is `db.m4.4xlarge`
        - this may be ok in maintenance mode, but if you are going to enable write traffic, the instance type must be scaled up. 
            - SRE's performed a manual instance type change on the Frankfurt read-replica, and it took ~10 minutes to change from a `db.t2.medium` to a `db.m4.xlarge`. 
    - although we have alerting in place to notify the SRE team in the event of a replication error, it's a good idea to check the replication status on the RDS details page for the `sumo` MySQL instance.
        - specifically, check the `DB Instance Status`, `Read Replica Source`, `Replication State`, and `Replication Error` values.
    - decide if [promoting the read-replica](http://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/USER_ReadRepl.html#USER_ReadRepl.Promote) to a master is appropriate.
        - it's preferrable to have a multi-AZ RDS instance, as we can take snapshots against the failover instance (RDS does this by default in a multi-AZ setup).
        - if data is written to a promoted instance, and failover back to the us-west-2 clusters is desirable, a full DB backup and restore in us-west-2 is required.
        - the replica is automatically rebooted before being promoted to a full instance.
- **ensure image versions are up to date**
- Most MySQL changes should already be replicated to the read-replica, however, if you're reading this, chances are things are broken. Ensure that the DB schema is correct for the iamges you're deploying.
- **scale cluster and pods**
    - the prod deployments [A](https://github.com/mozilla/kitsune/blob/master/k8s/regions/oregon-a/prod.yaml#L24-L48) and [B](https://github.com/mozilla/kitsune/blob/master/k8s/regions/oregon-b/prod.yaml#L24-L48) yaml contain the correct number of replicas, but here are some safe values to use in an emergency:

        ```
        # Oregon A - ALSO runs cron pod
        kubectl -n sumo-prod scale --replicas=50 deployment/sumo-prod-web
        kubectl -n sumo-prod scale --replicas=3 deployment/sumo-prod-celery
        kubectl -n sumo-prod scale --replicas=1 deployment/sumo-prod-cron

        # Oregon B - Does NOT run cron pod
        kubectl -n sumo-prod scale --replicas=50 deployment/sumo-prod-web
        kubectl -n sumo-prod scale --replicas=3 deployment/sumo-prod-celery
        kubectl -n sumo-prod scale --replicas=0 deployment/sumo-prod-cron
        ```
- **DNS**
    - point the `prod-tp.sumo.mozit.cloud` traffic policy at the Frankfurt ELB
