from invoke import task
from invoke.exceptions import Exit
from env import *
from deploy_utils import get_kubectl


@task
def check_environment(ctx):
    """
    Ensure that a .yaml file has been specified
    """
    # I'm not sure how to share these between invoke namespaces (yet?)
    if 'K8S_NAMESPACE' not in ctx.config:
        print("Please specify a configuration file with -f")
        raise Exit()


@task(check_environment)
def status_web(ctx):
    """
    Check rollout status of a SUMO web deployment
    """
    namespace = ctx.config['K8S_NAMESPACE']
    web_deployment_name = ctx.config['SUMO_WEB_DEPLOYMENT_NAME']
    ctx.run('{} -n {}} rollout status deploy {}'.format(get_kubectl(),
                                                        namespace, web_deployment_name))


@task(check_environment)
def rollback_web(ctx):
    """
    Undo a deployment
    """
    namespace = ctx.config['K8S_NAMESPACE']
    web_deployment_name = ctx.config['SUMO_WEB_DEPLOYMENT_NAME']
    ctx.run('{}} -n {}} rollout undo deploy {}'.format(get_kubectl(),
                                                       namespace, web_deployment_name))
