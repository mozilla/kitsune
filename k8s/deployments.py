from invoke import task
from invoke.exceptions import Exit
from env import SUMO_APP_TEMPLATE, SUMO_NODEPORT_TEMPLATE, SUMO_SERVICE_TEMPLATE
from deploy_utils import render_template, k8s_apply, k8s_delete_resource


@task()
def check_environment(ctx):
    """
    Ensure that a .yaml file has been specified
    """
    if "namespace" not in ctx.config["kubernetes"]:
        print("Please specify a configuration file with -f")
        raise Exit()


def _create(app, ctx, tag, apply, record=False):
    if tag:
        ctx.config["kubernetes"]["image"]["tag"] = tag
    t = render_template(config=ctx.config, template_name=SUMO_APP_TEMPLATE, app=app)
    k8s_apply(ctx, t, apply, record)


@task(check_environment)
def create_web(ctx, tag=None, apply=False):
    """
    Create or update a SUMO web deployment
    """
    _create("web", ctx, tag, apply, record=True)


@task(check_environment)
def create_celery(ctx, tag=None, apply=False):
    """
    Create or update a SUMO celery deployment
    """
    _create("celery", ctx, tag, apply, record=True)


@task(check_environment)
def create_cron(ctx, tag=None, apply=False):
    """
    Create or update a SUMO cron deployment
    """
    _create("cron", ctx, tag, apply, record=True)


def _delete(app, ctx, apply):
    deployment = "deploy/{}".format(ctx.config["kubernetes"]["apps"][app]["deployment_name"])
    k8s_delete_resource(ctx, deployment, apply)


@task(check_environment)
def delete_web(ctx, apply=False):
    """
    Delete an existing SUMO web deployment
    """
    _delete("web", ctx, apply)


@task(check_environment)
def delete_celery(ctx, apply=False):
    """
    Delete an existing SUMO celery deployment
    """
    _delete("celery", ctx, apply)


@task(check_environment)
def delete_cron(ctx, apply=False, infra_apply=False):
    """
    Delete an existing SUMO cron deployment
    """
    _delete("cron", ctx, apply)


@task(check_environment)
def create_service(ctx, apply=False, infra_apply=False):
    """
    Create or update a SUMO service with ELB
    """
    t = render_template(config=ctx.config, template_name=SUMO_SERVICE_TEMPLATE)
    k8s_apply(ctx, t, apply)


@task(check_environment)
def delete_service(ctx, apply=False, infra_apply=False):
    """
    Delete an existing SUMO service ELB
    """
    if infra_apply:
        deployment = "deploy/{}".format(ctx.config["kubernetes"]["service_name"])
        k8s_delete_resource(ctx, deployment, apply)
    else:
        print("Infra tasks require an additional --infra-apply confirmation")


@task(check_environment)
def create_all(ctx, tag=None, apply=False):
    """
    Create web, cron and celery deployments
    """
    create_web(ctx, tag, apply)
    create_cron(ctx, tag, apply)
    create_celery(ctx, tag, apply)


@task(check_environment)
def delete_all(ctx, apply=False):
    """
    Delete existing web, cron and celery deployments
    """
    delete_web(ctx, apply)
    delete_cron(ctx, apply)
    delete_celery(ctx, apply)
