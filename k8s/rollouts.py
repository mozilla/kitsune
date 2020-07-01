from deploy_utils import get_kubectl
from deployments import check_environment
from invoke import task


def rollout_status(ctx, deployment_name):
    namespace = ctx.config['kubernetes']['namespace']
    ctx.run('{} -n {} rollout status deploy {}'.format(get_kubectl(),
                                                       namespace, deployment_name))


def rollback(ctx, deployment_name):
    namespace = ctx.config['kubernetes']['namespace']
    ctx.run('{} -n {} rollout undo deploy {}'.format(get_kubectl(),
                                                     namespace, deployment_name))


@task(check_environment)
def status_web(ctx):
    """
    Check rollout status of a SUMO web deployment
    """
    deployment_name = ctx.config['kubernetes']['apps']['web']['deployment_name']
    rollout_status(ctx, deployment_name)


@task(check_environment)
def status_celery(ctx):
    """
    Check rollout status of a SUMO web deployment
    """
    deployment_name = ctx.config['kubernetes']['apps']['celery']['deployment_name']
    rollout_status(ctx, deployment_name)


@task(check_environment)
def status_cron(ctx):
    """
    Check rollout status of a SUMO web deployment
    """
    deployment_name = ctx.config['kubernetes']['apps']['cron']['deployment_name']
    rollout_status(ctx, deployment_name)


@task(check_environment)
def rollback_web(ctx):
    """
    Undo a web deployment
    """
    deployment_name = ctx.config['kubernetes']['apps']['web']['deployment_name']
    rollback(ctx, deployment_name)


@task(check_environment)
def rollback_celery(ctx):
    """
    Undo a celery deployment
    """
    deployment_name = ctx.config['kubernetes']['apps']['celery']['deployment_name']
    rollback(ctx, deployment_name)


@task(check_environment)
def rollback_cron(ctx):
    """
    Undo a cron deployment
    """
    deployment_name = ctx.config['kubernetes']['apps']['cron']['deployment_name']
    rollback(ctx, deployment_name)
