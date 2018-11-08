*devel* jobs
==============

A *devel* job is used for continuous integration.
It builds the code and runs the tests to check for regressions.
It operates on a single source repository and is triggered for every
commit to a specific branch.

A variation of this is a *pull request* job.
The only difference is that it is triggered by create a pull request or
changing commits on an existing pull request.

Each build is performed within a clean environment (provided by a Docker
container) which only contains the specific dependencies of packages in the
repository as well as tools needed to perform the build.

The `diagram <devel_call_graph.png>`_ shows the correlation between the various
scripts and templates.

The set of source repositories is identified by the *source build files* in the
ROS build farm configuration repository.
For each *source build file* two separate Jenkins views are created.


Entry points
------------

The following scripts are the entry points for *devel* jobs.
The scripts operate on a specific *source build file* in the ROS build farm
configuration:

* **generate_devel_maintenance_jobs.py** generates a set of jobs on the farm
  which will perform maintenance tasks.

  * The ``reconfigure-jobs`` job will (re-)configure the *devel* and *pull
    request* jobs for each package on a regular basis (e.g. once every day).
  * The ``trigger-jobs`` job is triggered manually to trigger *devel* jobs
    selected by their current build status.

* **generate_devel_jobs.py** invokes *generate_devel_job.py* for every source
  repository matching the criteria from the *source build file*.
* **generate_devel_job.py** generates *devel* and/or *pull request* jobs for a
  specific source repository for each platform and architecture listed in the
  *release build file*.
* **generate_devel_script.py** generates a *shell* script which will run the
  same tasks as the *devel* job for a specific source repository on a
  local machine.


The build process in detail
---------------------------

The actual build is performed within a Docker container in order to only make
the declared dependencies available.
Since the dependencies needed at build time are different from the dependencies
to run / test the code these two tasks use two different Docker containers.

The actual build process starts in the script *create_devel_task_generator.py*.
It generates two Dockerfiles: one to perform the *build-and-install* task and
one to perform the *build-and-test* task.


Build and install
^^^^^^^^^^^^^^^^^

This task is performed by the script *build_and_install.py*.
The environment will only contain the *build* dependencies declared by the
packages in the source repository.

The task performs the following steps:

* The content of the source repository is expected to be available in the
  folder *ws/src*.
* Removes any *build*, *devel* and *install* folders left over from previous
  runs.
* Depending on the chosen build tool it invokes either of the two:

  * ``catkin_make_isolated --install ...``
  * ``colcon build --executor sequential --event-handlers console_direct+ ...``

    The direct output allows the output to be streamed while it is progressing.
    The sequential execution avoids interleaved output between packages.

  Both commands use the environment variable ``MAKEFLAGS=-j1``.

  The build is performed single threaded to achieve deterministic build results
  (a different target order could break the build if it lacks correct target
  dependencies).

  Additionally the following CMake flags are being passed:
  ``--cmake-args -DBUILD_TESTING=0 -DCATKIN_SKIP_TESTING=1``.

  Since the CMake option ``BUILD_TESTING`` is enabled by default it is
  explicitly disabled.

  Since the CMake option ``CATKIN_ENABLE_TESTING`` is not enabled explicitly
  the packages must neither configure any tests nor use any test-only
  dependencies.
  The option ``CATKIN_SKIP_TESTING`` prevents CMake from failing if packages
  violate this restriction and only outputs a CMake warning instead.


Build and test
^^^^^^^^^^^^^^

This task is performed by the script *build_and_test.py*.
The environment will only contain the *build*, *run* and *test* dependencies
declared by the packages in the source repository.

The task performs the following steps:

* The content of the source repository is expected to be available in the
  folder *ws/src*.
* Depending on the chosen build tool it invokes either of the two:

  * ``catkin_make_isolated --catkin-make-args run_tests ...``
  * ``colcon test --executor sequential --event-handlers console_direct+``

    The direct output allows the output to be streamed while it is progressing.
    The sequential execution avoids interleaved output between packages.

  Both commands use the environment variable ``MAKEFLAGS=-j1``.

  The tests are performed single threaded to achieve deterministic test results
  (otherwise some tests might affect each other).

  Additionally the following CMake flags are being passed to reenable tests and
  determine the location of the test results:
  ``--cmake-args -DCATKIN_ENABLE_TESTING=1 -DCATKIN_SKIP_TESTING=0 -DCATKIN_TEST_RESULTS_DIR=path/to/ws/test_results``.
  For colcon the test result directory is additionally passed via
  ``--test-result-base``

  The XUnit test results for each package will be created in the subfolder
  *test_results* in the workspace and be shown by Jenkins.


Known limitations
^^^^^^^^^^^^^^^^^

Since the Docker container contains the dependencies for all packages of the
tested source repository it can not detect missing dependencies of individual
packages if another package in the same repository has that dependency.


Run the *devel* job locally
---------------------------

In order to use ``ros_buildfarm`` locally you need to
`setup your environment <../environment.rst>`_ with the necessary Python
packages.

The entry point ``generate_devel_script.py`` can be used to generate a shell
script which will perform the same tasks as the build farm.
It requires certain tools to be available on the local machine (e.g. the Python
packages ``catkin_pkg``, ``rosdistro``).

When the generated script is being invoked in runs the *build-and-install* task
as well as the *build-and-test* task in separate Docker containers.
Additionally it invokes the tool ``catkin_test_results --all`` /
``colcon test-result --all`` to output a summary of all tests.


Example invocation
^^^^^^^^^^^^^^^^^^

The following commands run the *devel* job for the *roscpp_core* repository
from ROS *Indigo* for Ubuntu *Trusty* *amd64*:

.. code:: sh

  mkdir /tmp/devel_job
  generate_devel_script.py https://raw.githubusercontent.com/ros-infrastructure/ros_buildfarm_config/production/index.yaml indigo default roscpp_core ubuntu trusty amd64 > /tmp/devel_job/devel_job_indigo_roscpp_core.sh
  cd /tmp/devel_job
  sh devel_job_indigo_roscpp_core.sh

Return code
-----------

The return code of the generated script will be zero if it successfully performed the build and ran the test even if some tests failed.
By setting the environment variable `ABORT_ON_TEST_FAILURE=1` the return code will also be non-zero in case of failed tests.

Instead of invoking the generated script it can also be *sourced*:

.. code:: sh

  . devel_job_indigo_roscpp_core.sh

The return code of the invocation of ``catkin_tests_results`` /
``colcon test-result``is then available in the environment variable
``test_result_RC``.

Run the *devel* job on Travis
-----------------------------

Since it is easy to run a *devel* job locally it can also be run on Travis to either test every commit or pull request.
The setup and invocation is the same as locally.
The following .travis.yml template is a good starting point and is ready to be use:

.. code:: yaml

  # while this doesn't require sudo we don't want to run within a Docker container
  sudo: true
  dist: trusty
  language: python
  python:
    - "3.4"
  env:
    global:
      - JOB_PATH=/tmp/devel_job
    matrix:
      - ROS_DISTRO_NAME=indigo OS_NAME=ubuntu OS_CODE_NAME=trusty ARCH=amd64
      #- ROS_DISTRO_NAME=jade OS_NAME=ubuntu OS_CODE_NAME=trusty ARCH=amd64
      #- ROS_DISTRO_NAME=kinetic OS_NAME=ubuntu OS_CODE_NAME=xenial ARCH=amd64
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

    # run devel job for a ROS repository with the same name as this repo
    - export REPOSITORY_NAME=`basename $TRAVIS_BUILD_DIR`
    # use the code already checked out by Travis
    - mkdir -p $JOB_PATH/ws/src
    - cp -R $TRAVIS_BUILD_DIR $JOB_PATH/ws/src/
    # generate the script to run a devel job for that target and repo
    - generate_devel_script.py https://raw.githubusercontent.com/ros-infrastructure/ros_buildfarm_config/production/index.yaml $ROS_DISTRO_NAME default $REPOSITORY_NAME $OS_NAME $OS_CODE_NAME $ARCH > $JOB_PATH/devel_job.sh
    - cd $JOB_PATH
    - cat devel_job.sh
    # run the actual job which involves Docker
    - sh devel_job.sh -y
  script:
    # get summary of test results
    # use either of the two following options depending on the chosen build tool
    - /tmp/catkin/bin/catkin_test_results $JOB_PATH/ws/test_results --all
    - colcon test-result --test-result-base $JOB_PATH/ws/test_results --all
  notifications:
    email: false

An example can be found in the `.travis.yml <https://github.com/ros-infrastructure/ros_buildfarm/blob/master/.travis.yml>`_ file of the *ros_buildfarm* repository.

Run for "custom" repositories
-----------------------------

A *devel* job requires that the tested repository is being listed in a ROS distribution file.
If a repository is a fork or is not yet registered it can use a `*prerelease job* <prerelease_jobs.rst#run-for-custom-repositories>`_ instead.
