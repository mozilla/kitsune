from deploy_utils import k8s_apply
from deploy_utils import k8s_delete_resource
from deploy_utils import render_template
from env import SUMO_APP_TEMPLATE
from env import SUMO_NODEPORT_TEMPLATE
from invoke import task
from invoke.exceptions import Exit


@task()
def check_environment(ctx):
    """
    Ensure that a .yaml file has been specified
    """
    if "namespace" not in ctx.config["kubernetes"]:
        print("Please specify a configuration file with -f")
        raise Exit()


def _create(app, ctx, tag, apply):
    if tag:
        ctx.config["kubernetes"]["image"]["tag"] = tag
    t = render_template(config=ctx.config, template_name=SUMO_APP_TEMPLATE, app=app)
    k8s_apply(ctx, t, apply)


@task(check_environment)
def create_web(ctx, tag=None, apply=False):
    """
    Create or update a SUMO web deployment
    """
    _create("web", ctx, tag, apply)


@task(check_environment)
def create_celery(ctx, tag=None, apply=False):
    """
    Create or update a SUMO celery deployment
    """
    _create("celery", ctx, tag, apply)


@task(check_environment)
def create_cron(ctx, tag=None, apply=False):
    """
    Create or update a SUMO cron deployment
    """
    _create("cron", ctx, tag, apply)


def _delete(app, ctx, apply):
    deployment = "deploy/{}".format(ctx.config["kubernetes"]["apps"][app]["deployment_name"])
    k8s_delete_resource(ctx, deployment, apply)


@task(check_environment)
def delete_web(ctx, apply=False):
    _delete("web", ctx, apply)


@task(check_environment)
def delete_celery(ctx, apply=False):
    _delete("celery", ctx, apply)


@task(check_environment)
def delete_cron(ctx, apply=False, infra_apply=False):
    _delete("cron", ctx, apply)


@task(check_environment)
def create_nodeport(ctx, apply=False, infra_apply=False):
    """
    Create or update a SUMO nodeport
    """
    t = render_template(config=ctx.config, template_name=SUMO_NODEPORT_TEMPLATE)
    k8s_apply(ctx, t, apply)


@task(check_environment)
def delete_nodeport(ctx, apply=False, infra_apply=False):
    """
    Delete an existing SUMO nodeport
    """
    if infra_apply:
        deployment = "deploy/{}".format(ctx.config["kubernetes"]["nodeport_name"])
        k8s_delete_resource(ctx, deployment, apply)
    else:
        print("Infra tasks require an additional --infra-apply confirmation")


@task(check_environment)
def create_all(ctx, tag=None, apply=False):
    create_web(ctx, tag, apply)
    create_cron(ctx, tag, apply)
    create_celery(ctx, tag, apply)


@task(check_environment)
def delete_all(ctx, apply=False):
    delete_web(ctx, apply)
    delete_cron(ctx, apply)
    delete_celery(ctx, apply)
