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
from ROS *Crystal* for Ubuntu *Bionic* *amd64*:

.. code:: sh

  mkdir /tmp/ci_job
  generate_ci_script.py https://raw.githubusercontent.com/ros2/ros_buildfarm_config/ros2/index.yaml crystal default ubuntu bionic amd64 --package-selection-args --packages-up-to ament_cmake_ros > /tmp/ci_job/ci_job_crystal_ament_cmake_ros.sh
  cd /tmp/ci_job
  sh ci_job_crystal_ament_cmake_ros.sh

Return code
-----------

The return code of the generated script will be zero if it successfully
performed the build and ran the test even if some tests failed.
By setting the environment variable ``ABORT_ON_TEST_FAILURE=1`` the return code
will also be non-zero in case of failed tests.

Instead of invoking the generated script it can also be *sourced*:

.. code:: sh

  . ci_job_crystal.sh

The return code of the invocation of ``catkin_tests_results`` /
``colcon test-result`` is then available in the environment variable
``test_result_RC``.

Run the *CI* job on Travis
--------------------------

Since it is easy to run a *CI* job locally it can also be run on Travis to
either test every commit or pull request.
The setup and invocation is the same as locally.
The following .travis.yml template is a good starting point and is ready to be
used:

.. code:: yaml

  # while this doesn't require sudo we don't want to run within a Docker container
  sudo: true
  dist: trusty
  language: python
  python:
    - "3.4"
  env:
    global:
      - JOB_PATH=/tmp/ci_job
    matrix:
      - ROS_DISTRO_NAME=crystal OS_NAME=ubuntu OS_CODE_NAME=trusty ARCH=amd64
  install:
    # either install the latest released version of ros_buildfarm
    - pip install ros_buildfarm
    # or checkout a specific branch
    #- git clone -b master https://github.com/ros-infrastructure/ros_buildfarm /tmp/ros_buildfarm
    #- pip install /tmp/ros_buildfarm

    # use either of the two following options depending on the chosen build tool
    # checkout catkin for catkin_test_results script
    - git clone https://github.com/ros/catkin /tmp/catkin
    # install colcon for test results
    - pip install colcon-core colcon-test-result

    # run CI job for a ROS repository with the same name as this repo
    - export PACKAGES_SELECT=`basename $TRAVIS_BUILD_DIR`
    # use the code already checked out by Travis
    - mkdir -p $JOB_PATH/ws/src
    - cp -R $TRAVIS_BUILD_DIR $JOB_PATH/ws/src/
    # generate the script to run a CI job for that target and repo
    - generate_ci_script.py https://raw.githubusercontent.com/ros2/ros_buildfarm_config/ros2/index.yaml $ROS_DISTRO_NAME default $OS_NAME $OS_CODE_NAME $ARCH --package-selection-args --packages-up-to $PACKAGE_SELECT > $JOB_PATH/ci_job.sh
    - cd $JOB_PATH
    - cat ci_job.sh
    # run the actual job which involves Docker
    - sh ci_job.sh -y
  script:
    # get summary of test results
    # use either of the two following options depending on the chosen build tool
    - /tmp/catkin/bin/catkin_test_results $JOB_PATH/ws/test_results --all
    - colcon test-result --test-result-base $JOB_PATH/ws/test_results --all
  notifications:
    email: false

An example can be found in the `.travis.yml <https://github.com/ros-infrastructure/ros_buildfarm/blob/master/.travis.yml>`_
file of the *ros_buildfarm* repository.

Run for "custom" repositories
-----------------------------

A *CI* job requires that repositories be listed in a ``.repos`` file hosted at
some URL.
