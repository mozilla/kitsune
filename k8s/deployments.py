from invoke import task
from invoke.exceptions import Exit
from env import *
from deploy_utils import render_template, k8s_apply, k8s_delete_resource


@task()
def check_environment(ctx):
    """
    Ensure that a .yaml file has been specified
    """
    if 'K8S_NAMESPACE' not in ctx.config:
        print("Please specify a configuration file with -f")
        raise Exit()


@task(check_environment)
def create_web(ctx, apply=False):
    """
    Create or update a SUMO web deployment
    """
    t = render_template(config=ctx.config,
                        template_name=SUMO_WEB_TEMPLATE)
    k8s_apply(ctx, t, apply)


@task(check_environment)
def delete_web(ctx, apply=False, infra_apply=False):
    """
    Delete an existing SUMO web deployment
    """

    deployment = 'deploy/{}'.format(ctx.config['SUMO_WEB_DEPLOYMENT_NAME'])
    if infra_apply:
        k8s_delete_resource(ctx, deployment, apply)
    else:
        print("Infra tasks require an additional --infra-apply confirmation")


@task(check_environment)
def create_nodeport(ctx, apply=False, infra_apply=False):
    """
    Create or update a SUMO nodeport
    """
    t = render_template(config=ctx.config,
                        template_name=SUMO_NODEPORT_TEMPLATE)
    k8s_apply(ctx, t, apply)


@task(check_environment)
def delete_nodeport(ctx, apply=False, infra_apply=False):
    """
    Delete an existing SUMO nodeport
    """
    if infra_apply:
        deployment = 'deploy/{}'.format(ctx.config['SUMO_NODEPORT_NAME'])
        k8s_delete_resource(ctx, deployment, apply)
    else:
        print("Infra tasks require an additional --infra-apply confirmation")
