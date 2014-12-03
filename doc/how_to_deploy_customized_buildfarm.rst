How to deploy a customized buildfarm locally?
=============================================


Change buildfarm configuration
------------------------------

Some configuration options in the build files should be self-explaining.

E.g. you can customize the Jenkins job priorities, the Jenkins job timeouts.


Change which packages / repositories are being processed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The release build file allows to restrict the set of packages by either
only building a certain set of packages (*whitelisting*) or ignoring a certain
set of packages (*blacklisting*).

You can list any released package name under ``repository_blacklist`` or
``repository_whitelist``.

The source / doc build file allows to restrict the set on a repository level.
The configuration options are ``package_blacklist`` and ``package_whitelist``.

If a package / repository is listed in both the blacklist takes precedence.


Change which targets are being built
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

The release build file can only list targets which have been created by
``bloom`` when the ROS package was released.


Change the sync criteria
^^^^^^^^^^^^^^^^^^^^^^^^

You can configure the sync criteria when packages are being synced from the
``building`` to the ``testing`` repository.

The release build file has two optional configuration options to restrict when
a sync should happen:

* ``sync: package_count:`` which defines the minimum required number of
  available packages

* ``sync: packages:`` a list of package names which must be available


Change ROS buildfarm code
-------------------------

You can fork the
[ros_buildfarm](https://github.com/ros-infrastructure/ros_buildfarm) repository
and commit arbitrary changes to the default branch of the forked repository
(and optionally change the default branch).

If you use this forked repository to generate the administrative jobs and
afterwards reconfigure all other jobs the buildfarm will utilize your modified
version of the code to perform all jobs and tasks.
