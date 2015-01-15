How to release custom packages to a forked rosdistro database?
==============================================================

There are two options for running a custom ROS buildfarm with custom packages.
You can either:

* use the existing ROS packages from the official Debian repository and only
  build / test / document your custom ROS packages or

* you can build a complete custom ROS distribution

The advantage of the first option is that is only requires a smaller amount of
computational resources.
The disadvantage is that your packages depend on the release schedule of the
official ROS distribution and the status of the official repository.

On the other hand the second option allows maximum control over which versions
of ROS packages you want to build for the extra cost of requiring to rebuild
all ROS packages.


Add a custom distribution file
------------------------------

In order to keep your custom packages separate from the packages listed in the
official distribution file it is recommended to create a custom distribution
file.
It should be a sibling to the existing file ``indigo/YOUR_NAME.yaml`` in your
fork of the rosdistro repository and a reference must be added in the index
file.

For more flexible configuration options you should also add a ``tag`` to your
custom distribution file::

    tags:
    - YOUR_TAG


Configure the build files
-------------------------

You can customize the build files to only build the targets you are interested
in.

If you chose option one (only build packages on-top of the official ROS
distribution) you must configure the build files to only operate on your custom
distribution file by adding the following option::

    tag_whitelist:
    - YOUR_TAG


Release packages using bloom
----------------------------

Every developer invoking ``bloom-release`` must have the environment variable
``ROSDISTRO_INDEX_URL`` set to point to your forked rosdistro index file.
This is the same as for any user using your custom distribution.


Deploy your configuration to jenkins
------------------------------------

As documented in the `general process documentation<general_process.rst>`_.


Run administrative tasks
------------------------

As documented in the `general process documentation<general_process.rst>`_.
