*CI* jobs
=========

A *CI* job is used for continuous integration across repositories.
It builds the code and runs the tests to check for regressions.
It operates on many source repositories as specified in one or more ``.repos``
files, and is triggered to produce a nightly comprehensive archive, and can
also be triggered manually to quickly test changes on a select set of
packages.

Each build is performed within a clean environment (provided by a Docker
container) which only contains the specific dependencies of packages in the
repository as well as tools needed to perform the build and any packages
specified as part of the ``install_packages``.

Entry points
------------

The following scripts are the entry points for *CI* jobs.
The scripts operate on the default ``.repos`` file in the ROS build farm
configuration, unless specified otherwise:

* **generate_ci_maintenance_jobs.py** generates a set of jobs on the farm
  which will perform maintenance tasks.

  * The ``reconfigure-jobs`` job will (re-)configure the *CI* nightly and
    overlay jobs on a regular basis (e.g. once every day).

* **generate_ci_jobs.py** invokes *generate_ci_job.py* for both the nightly
  configuration as well as the overlay configuration.
* **generate_ci_job.py** generates a *CI* nightly job for for each platform
  and architecture listed in the *CI build file*.
* **generate_ci_script.py** generates a *shell* script which will run the
  same tasks as the *CI* job on a local machine.

The build process in detail
---------------------------

The actual build is performed within a Docker container in order to ensure
only declared dependencies are available.

The actual build process starts in the script *create_ci_task_generator.py*.
It generates three Dockerfiles: one to perform the *create-workspace* task to
populate the workspace and enumerate prerequisites, one to perform the
*build-and-install* task, and one to perform the *build-and-test* task.

Create workspace
^^^^^^^^^^^^^^^^

This task is performed by the script *create_workspace.py*, the ``colcon``
executable and the ``rosdep`` executable.

The task performs the following steps:

* Prepare the package sources

  * Fetches the ``.repos`` file(s)
  * Fetches the source repositories containing the package(s) to be built
  * If necessary, merges a specified branch with the current release of those
    repositories

* Select the packages which should be built, tested, and installed

  * Marks the packages explicitly listed as ignored
  * If necessary, ignores packages to reduce the buildable packages based on:

    * Whether the package is specifically listed for inclusion
    * Whether the package is within a given number of dependency steps after
      a selected package
    * Whether the package is a dependency of one of the selected packages

* Enumerate dependencies

  * Lists the dependencies necessary to build and test the remaining ROS
    packages in the workspace, as well as the dependencies of any ROS packages
    in the underlay workspace(s) needed to support them.
  * Uses the rosdep tool to resolve those dependency keys to package names

Build and install
^^^^^^^^^^^^^^^^^

This task is identical to `the one used by the devel jobs <devel_jobs.rst#Build-and-install>`_.

Build and test
^^^^^^^^^^^^^^

This task is identical to `the one used by the devel jobs <devel_jobs.rst#Build-and-test>`_.

Known limitations
^^^^^^^^^^^^^^^^^

System dependency enumeration happens for all ROS packages that are part of the
non-underlay workspace.
This means that any non-ROS packages present in that workspace may need their
dependencies explicitly called out for inclusion in the ``install_package``
list, and also means that a missing dependency may be occluded by another
package in the workspace correctly declaring the same dependency.

Run the *CI* job locally
------------------------

Example invocation
^^^^^^^^^^^^^^^^^^

The following commands run the *CI* job for the *ament_cmake_ros* package
from ROS *Rolling* for Ubuntu *Noble* *amd64*:

.. code:: sh

  mkdir /tmp/ci_job
  generate_ci_script.py https://raw.githubusercontent.com/ros2/ros_buildfarm_config/ros2/index.yaml rolling default ubuntu noble amd64 --package-selection-args --packages-up-to ament_cmake_ros > /tmp/ci_job/ci_job_rolling_ament_cmake_ros.sh
  cd /tmp/ci_job
  sh ci_job_rolling_ament_cmake_ros.sh

Return code
-----------

The return code of the generated script will be zero if it successfully
performed the build and ran the test even if some tests failed.
By setting the environment variable ``ABORT_ON_TEST_FAILURE=1`` the return code
will also be non-zero in case of failed tests.

Instead of invoking the generated script it can also be *sourced*:

.. code:: sh

  . ci_job_rolling_ament_cmake_ros.sh

The return code of the invocation of ``catkin_tests_results`` /
``colcon test-result`` is then available in the environment variable
``test_result_RC``.

Run for "custom" repositories
-----------------------------

A *CI* job requires that repositories be listed in a ``.repos`` file hosted at
some URL.
