How to configure a "customized" build farm?
===========================================

This how-to describes how you can customize your ROS build farm:

* to build / document a subset of packages / repositories
* to build different targets
* to change the sync criteria

Besides the option described below the
`basic configuration options <basic_configuration.rst>`_ must additionally be
applied.


Change which packages / repositories are being processed
--------------------------------------------------------

The release build files allow to restrict the set of packages by either only
building a certain set of packages (*whitelisting*) or ignoring a certain set
of packages (*blacklisting*).

You can list any released package name under ``package_blacklist`` or
``package_whitelist``.

The source / doc build files allow to restrict the set on a repository level.
The configuration options are ``repository_blacklist`` and ``repository_whitelist``.

If a package / repository is listed in both the blacklist takes precedence.


Change which targets are being built
------------------------------------

Modify the targets listed in the build files.
The targets are defined as nested dictionaries of the OS name
(e.g. ``ubuntu``), the OS code name (e.g. ``trusty``) and the architecture
(e.g. ``amd64``)::

    targets:
      OS_NAME_1:
        OS_CODE_NAME_1:
          ARCH_1:
          ARCH_2:
        OS_CODE_NAME_2:
          ARCH_2:
      OS_NAME_2:
        OS_CODE_NAME_3:
          ARCH_3:

The release build files can only list targets which have been created by
``bloom`` when the ROS package was released.


Change the sync criteria
------------------------

You can configure the sync criteria when packages are being synced from the
``building`` to the ``testing`` repository.

The release build files have two optional configuration options to restrict
when a sync should happen:

* ``sync: package_count:`` which defines the minimum required number of
  available packages

* ``sync: packages:`` a list of package names which must be available


Change the priority and timeouts of the Jenkins jobs
----------------------------------------------------

You can customize the priorities of the generated jobs to fit your needs.
Depending on the performance of your build agent you might also want to adjust
the job timeouts.

For both options please see the
`configuration options <configuration_options.rst>`_ for details.
