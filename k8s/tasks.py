"""
This module exists to setup the pyinvoke namespace.
"""
from invoke import Collection, task
import deployments
import rollouts

namespace = Collection(deployments, rollouts)
