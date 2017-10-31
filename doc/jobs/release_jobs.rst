*release* jobs
==============

A *release* job is used to build *source* and *binary* packages.
It operates on a single package released in a GBP (git-buildpackage)
repository.
The *source* jobs are triggered by a version change in the rosdistro
distribution file.
The *binary* jobs are triggered by their *source* counter part.

Each build is performed within a clean environment (provided by a Docker
container) which only contains the specific dependencies of packages in the
repository as well as tools needed to perform the packaging.

The `diagram <release_call_graph.png>`_ shows the correlation between the
various scripts and templates.

The set of packages is identified by the *release build files* in the ROS build
farm configuration repository.
For each *release build file* several separate Jenkins view are created.

Whenever a *source* or *binary* job has created a package it is being imported
into the repository.
Once all jobs have finished it is checked if the sync criteria is fulfilled and
all packages are synced from the *building* to the *testing* repository.


Entry points
------------

The following scripts are the entry points for *release* jobs.
The scripts operate on a specific *release build file* in the ROS build farm
configuration:

* **generate_release_maintenance_jobs.py** generates a set of jobs on the farm
  which will perform maintenance tasks.

  * The ``reconfigure-jobs`` job will (re-)configure the *source* and *binary*
    jobs for each package on a regular basis (e.g. once every day).
  * The ``trigger-jobs`` job will trigger *source* and/or *binary* jobs when
    the version in the rosdistro database changes (polling e.g. every 15
    minutes).
  * The ``import_upstream`` job is triggered manually to import third-party
    packages into the repository.
  * The ``trigger-broken-with-non-broken-upstream`` job is triggered manually
    to trigger broken jobs which have no broken upstream jobs.

* **generate_release_jobs.py** invokes *generate_release_job.py* for every
  package matching the criteria from the *release build file*.
  Additionally it generates the following jobs:

  * The ``import-package`` job is triggered automatically from *source* and
    *binary* job and imports the package uploaded to the *repo* machine
    into the *building* repository.

  * The ``sync-packages-to-testing`` job is triggered automatically after all
    *binary* job of a specific architecture have finished.
    It syncs all *source* and *binary* packages of that architecture from the
    *building* to the *testing* repository if the sync criteria is fulfilled.

    Note that multiple architectures share the same *source* packages.
    Whenever the *binary* jobs of a specific architecture finish that will also
    sync the *source* packages to the *testing* repository.
    That happens even if the *binary* jobs for other architectures sharing the
    same *source* packages have not finished building yet.

  * The ``sync-packages-to-main`` job must be triggered manually to sync all
    packages from the *testing* to the *main* repository.

* **generate_release_job.py** generates *source* jobs for a specific package
  for each OS code name as well as *binary* jobs for thee package for each OS
  code name and architecture listed in the *release build file*.

* **generate_release_script.py** generates a *shell* script which will run the
  same tasks as the *source* and *binary* jobs for a specific package on a
  local machine.

* **generate_release_trigger_upload_jobs.py** generates a pair of jobs that
  trigger an upload to packages.ros.org. Only needed for the official buildfarm
  at build.ros.org.

The build process in detail
---------------------------

The *binary package* is build within a Docker container in order to only
make the declared dependencies available.
It requires all build dependencies to be installable from binary packages
(usually from the ``testing`` repository).


Build source package
^^^^^^^^^^^^^^^^^^^^

This task is performed by the script *run_sourcedeb_job.py*.
The task performs the following steps:

* **get_sources.py** clones the package specific tag containing the package
  sources as well as the OS code name specific packaging information from the
  GBP repository.
* **build_sourcedeb.py** invokes ``git-buildpackage`` to create a source
  package.

The Jenkins job will additionally perform the following steps:

* Uploads the source package to the target repository defined in the
  *release build file*.
* Triggers the ``import-package`` job passing the specific folder of the
  uploaded source package which imports the package into the target repository.


Build binary package
^^^^^^^^^^^^^^^^^^^^

This task is performed by the script *run_binarydeb_job.py*.
The task performs the following steps:

* **get_sourcedeb.py** fetches the source package using ``apt source``.
* **append_build_timestamp.py** can optionally be used to append the timestamp
  of the build behind the version number of the package.
* **build_binarydeb.py** invokes ``apt-src build`` to create a binary package.

The Jenkins job will additionally perform the following steps:

* Uploads the binary package to the target repository defined in the
  *release build file*.
* Triggers the ``import-package`` job passing the specific folder of the
  uploaded binary package which imports the package into the target repository.


Run the *release* job locally
-----------------------------

In order to use ``ros_buildfarm`` locally you need to
`setup your environment <../environment.rst>`_ with the necessary Python
packages.

The entry point *generate_release_script.py* can be used to generate a shell
script which will perform similar tasks as the build farm.
It does not upload the *source* or *binary* packages but keeps them locally.
It requires certain tools to be available on the local machine (e.g. the Python
packages ``catkin_pkg``, ``rosdistro``).

When the generated script is being invoked it builds M *source packages* (one
for each platform) and N *binary packages* (one for each platform and
architecture).


Example invocation
^^^^^^^^^^^^^^^^^^

The following commands build the *source* and *binary* packages of *roscpp*
from ROS *Indigo* for Ubuntu *Trusty* *amd64*:

.. code:: sh

  mkdir /tmp/release_job
  generate_release_script.py https://raw.githubusercontent.com/ros-infrastructure/ros_buildfarm_config/production/index.yaml indigo default roscpp ubuntu trusty amd64 > /tmp/release_job/release_job_indigo_roscpp.sh
  cd /tmp/release_job
  sh release_job_indigo_roscpp.sh
