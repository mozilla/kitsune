#!/usr/bin/env python
import os
from dennis.cmdline import click_run

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def path(components):
    return os.path.join(ROOT, *components)


if __name__ == '__main__':
    click_run()
