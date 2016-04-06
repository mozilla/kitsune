Kitsune via Vagrant
===================

Its easy to run Kitsune in a `Vagrant`_-managed virtual machine so we can run
the entire Kitsune easily.
If you're on Mac OS X or Linux or even Windows and looking for a quick way to get started, you
should try these instructions.

.. note:: **If you have problems getting vagrant up**, please :ref:`contact-us-chapter`.

.. _vagrant: https://www.vagrantup.com/
.. _uses NFS to share the current working directory: https://www.vagrantup.com/docs/synced-folders/nfs.html

Install and run everything
--------------------------

#. Install VirtualBox 4.x from https://www.virtualbox.org/

   .. note:: (Windows) After installing VirtualBox you need to set
              PATH=C:\\Program Files\\Oracle\\VirtualBox\\VBoxManage.exe;

#. Install vagrant >= 1.6 using the installer from `vagrantup.com <https://www.vagrantup.com/>`_

#. Clone Kitsune::

       git clone https://www.github.com/mozilla/kitsune.git
       cd kitsune

#. Start the VM and install everything. (approx. 30 min on a fast net connection).::

      vagrant up

   .. note:: VirtualBox creates VMs in your system drive.
             If it won't fit on your system drive, you will need to `change that directory to another drive <https://emptysqua.re/blog/moving-virtualbox-and-vagrant-to-an-external-drive/>`_.

   At the end, you should see::

      => default: Done!


   If the above process fails with an error, please email us the error
   at dev-sumo@lists.mozilla.org and we'll see if we can fix it

#. Log into the VM with ssh::

       vagrant ssh

#. Create a Superuser::

       cd kitsune
       source venv/bin/activate
       ./manage.py createsuperuser

   You should give the Username and Password for login into your local Kitsune.

#.  Run Kitsune::

       ./manage.py runserver 0.0.0.0:8000

Now, just navigate to <http://localhost:8000> to see the application!

If you have other problems during ``vagrant up``, please email us the
error at dev-sumo@lists.mozilla.org and we'll see if we can fix it.
