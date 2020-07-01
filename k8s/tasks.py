"""
This module exists to setup the pyinvoke namespace.
"""
import deployments
import rollouts
from invoke import Collection
from invoke import task

namespace = Collection(deployments, rollouts)
