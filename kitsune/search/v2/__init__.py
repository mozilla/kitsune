import imp
import sys

# Monkey patch PYTHONPATH to temporarily work with multiple
# versions of elasticsearch
sys.path.insert(0, '/vendor')

# Manually import elasticsearch v7.x
f, filename, description = imp.find_module('elasticsearch')
elasticsearch7 = imp.load_module('elasticsearch7', f, filename, description)
