#!/usr/bin/env python
import os
import site
import sys


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
path = lambda *a: os.path.join(ROOT, *a)

prev_sys_path = list(sys.path)

site.addsitedir(path('vendor'))

# Move the new items to the front of sys.path.
new_sys_path = []
for item in list(sys.path):
    if item not in prev_sys_path:
        new_sys_path.append(item)
        sys.path.remove(item)
sys.path[:0] = new_sys_path

# Now we can import from third-party libraries.
from dennis.cmdline import cmdline_handler


if __name__ == '__main__':
    sys.exit(cmdline_handler("dennis-cmd", sys.argv[1:]))
