*release* jobs
==============

A *release* job is used to build *source* and *binary* packages.
It operates on a single package released in a GBP (git-buildpackage)
repository.
The ``source`` jobs are triggered by a version change in the rosdistro
distribution file.
The ``binary`` jobs are triggered by their *source* counter part.

Each build is performed within a clean environment (provided by a Docker
container) which only contains the specific dependencies of packages in the
repository as well as tools needed to perform the packaging.

The diagram (`release_call_graph`_) shows the correlation between the various
scripts and templates.

The set of packages is identified by the *release build files* in the used
rosdistro.
For each *release build file* a separate Jenkins view is created.


Entry points
------------

The following scripts are the entry points for *release* jobs:

* ``generate_release_maintenance_jobs.py`` generates a set of jobs on the farm
  which will perform maintenance tasks.

  * The most important one will be responsible to (re-)configure the
    *source* and *binary* jobs for each package on a regular basis.
  * ... more to ?

* ``generate_release_jobs.py`` invokes ``generate_release_job`` for every
  package identified by the *release build file*.
* ``generate_release_job.py`` generates *source* jobs for one package for
  each OS code name as well as *binary* jobs for one package for each OS code
  name and architecture listed in the *release build file*.
* ``generate_release_script.py`` generates a *shell* script which will run the
  same tasks as the *release job* on a local machine.


The build process in detail
---------------------------

The *binary package* is build within a Docker container in order to only
make the declared dependencies available.
It requires all build dependencies to be installable from binary packages.


Build source package
^^^^^^^^^^^^^^^^^^^^

This task is performed by the script ``run_sourcedeb_job.py``.
The task performs the following steps:

* ``get_sources.py`` clones the package specific tag containing the package
  sources as well as the OS code name specific packaging information from the
  GBP repository.
* ``build_sourcedeb.py`` invokes ``git-buildpackage`` to create a source
  package.
* ``upload_sourcedeb.py`` uploads the source package to the target package
  repository defined in the *release build file*.


Build binary package
^^^^^^^^^^^^^^^^^^^^

This task is performed by the script ``run_binarydeb_job.py``.
The task performs the following steps:

* ``get_sourcedeb.py`` fetches the source package using ``apt-get source``.
* ``append_build_timestamp.py`` can optionally be used to append the timestamp
  of the build behind the version number of the package.
* ``build_binarydeb.py`` invokes ``apt-src build`` to create a binary package.
* ``upload_binarydeb.py`` uploads the binary package to the target package
  repository defined in the *release build file*.


Run the *release* job locally
-----------------------------

The entry point ``generate_release_script.py`` can be used to generate a shell
script which will perform similar tasks as the buildfarm.
It does not upload the *source* or *binary* packages but keeps them locally.
It requires certain tools to be available on the local machine (e.g. the Python
packages ``catkin_pkg``, ``rosdistro``).

When the generated script is being invoked in builds M *source packages* (one
for each OS code name) and N *binary packages* (one for each OS code name and
architecture).


.. _release_call_graph: release_call_graph.png
