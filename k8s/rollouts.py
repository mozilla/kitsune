from invoke import task
from invoke.exceptions import Exit
from env import *
from deploy_utils import get_kubectl


def rollout_status(ctx, deployment_name):
    namespace = ctx.config['K8S_NAMESPACE']
    ctx.run('{} -n {} rollout status deploy {}'.format(get_kubectl(),
                                                        namespace, deployment_name))

def rollback(ctx, deployment_name):
    namespace = ctx.config['K8S_NAMESPACE']
    ctx.run('{} -n {} rollout undo deploy {}'.format(get_kubectl(),
                                                       namespace, deployment_name))

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
    rollout_status(ctx, ctx.config['SUMO_WEB_DEPLOYMENT_NAME'])

@task(check_environment)
def status_celery(ctx):
    """
    Check rollout status of a SUMO web deployment
    """
    rollout_status(ctx, ctx.config['SUMO_CELERY_DEPLOYMENT_NAME'])

@task(check_environment)
def status_cron(ctx):
    """
    Check rollout status of a SUMO web deployment
    """
    rollout_status(ctx, ctx.config['SUMO_CRON_DEPLOYMENT_NAME'])

@task(check_environment)
def rollback_web(ctx):
    """
    Undo a web deployment
    """    
    rollback(ctx, ctx.config['SUMO_WEB_DEPLOYMENT_NAME'])

@task(check_environment)
def rollback_celery(ctx):
    """
    Undo a celery deployment
    """    
    rollback(ctx, ctx.config['SUMO_CELERY_DEPLOYMENT_NAME'])

@task(check_environment)
def rollback_cron(ctx):
    """
    Undo a cron deployment
    """
    rollback(ctx, ctx.config['SUMO_CRON_DEPLOYMENT_NAME'])