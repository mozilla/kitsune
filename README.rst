=======
Kitsune
=======


Kitsune is the platform that powers `SuMo (support.mozilla.org)
<https://support.mozilla.org>`_

It is a Django_ application. There is documentation_ online.

.. _Mozilla Support: https://support.mozilla.org/
.. _Django: http://www.djangoproject.com/
.. _documentation: https://kitsune.readthedocs.io/


The *legacy* branch contains the codebase and deployment scripts for use in the
SCL3 datacenter. Only security fixes and changes to support product launches are
allowed to go in.

The *master* branch is where the active development of Kitsune happens to
modernize, containerize and bring to Kubernetes. Feature Pull Requests are not
allowed in unless related with the current effort to move to Kubernetes.

You can access the staging site at https://support.allizom.org/

See `what's deployed <https://whatsdeployed.io/s-PRg>`_
