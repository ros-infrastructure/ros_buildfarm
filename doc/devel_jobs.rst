*devel* jobs
==============

A *devel* job is used for continuous integration.
It builds the code and runs the tests to check for regressions.
It operates on a single source repository and is triggered for every commit to
a specific branch.

Each build is performed within a clean environment (provided by a Docker
container) which only contains the specific dependencies of packages in the
repository as well as tools needed to perform the build.

The diagram (`devel_call_graph`_) shows the correlation between the various
scripts and templates.

The set of source repositories is identified by the *source build files* in the
used rosdistro.
For each *source build file* a separate Jenkins view is created.


Entry points
------------

The following scripts are the entry points for *devel* jobs:

* ``generate_devel_maintenance_jobs.py`` generates a set of jobs on the farm
  which will perform maintenance tasks.

  * The most important one will be responsible to (re-)configure the *devel*
    jobs for each repository on a regular basis.
  * ... more to come?

* ``generate_devel_jobs.py`` invokes ``generate_devel_job`` for every source
  repository identified by the *source build file*.
* ``generate_devel_job.py`` generates a *devel* job for one source repository.
* ``generate_devel_script.py`` generates a *shell* script which will run the
  same tasks as the *devel job* on a local machine.


The build process in detail
---------------------------

The actual build is performed within a Docker container in order to only make
the declared dependencies available.
Since the dependencies needed at build time are different from the dependencies
to run / test the code these two tasks use two different Docker containers.

The actual build process starts in the script
``create_devel_task_generator.py``.
It generates two Dockerfiles: one to perform the *build-and-install* task and
one to perform the *build-and-test* task.


Build and install
^^^^^^^^^^^^^^^^^

This task is performed by the script ``catkin_make_isolated_and_install.py``.
The environment will only contain the build dependencies declared by the
packages in the source repository.

The task performs the following steps:

* The content of the source repository is expected to be available in the
  folder ``catkin_workspace/src``.
* Remove any ``build``, ``devel`` and ``install`` folder left over from
  previous runs.
* Invoke ``catkin_make_isolated --install``.
  Since the CMake option ``CATKIN_ENABLE_TESTING`` is not enabled explicitly
  the packages must neither configure any tests nor use any test-only
  dependencies.


Build and test
^^^^^^^^^^^^^^

This task is performed by the script ``catkin_make_isolated_and_test.py``.
The environment will only contain the build, run and test dependencies declared
by the packages in the source repository.

The task performs the following steps:

* The content of the source repository is expected to be available in the
  folder ``catkin_workspace/src``.
* Invoke
  ``catkin_make_isolated --cmake-args -DCATKIN_ENABLE_TESTING=1 --catkin-make-args run_tests``.
  The XUnit test results for each package will be created in the ``build``
  folder and shown by Jenkins.


Run the *devel* job locally
---------------------------

The entry point ``generate_devel_script.py`` can be used to generate a shell
script which will perform the same tasks as the buildfarm.
It requires certain tools to be available on the local machine (e.g. the Python
packages ``catkin_pkg``, ``rosdistro``).

When the generated script is being invoked in runs the *build-and-install* task
as well as the *build-and-test* task in separate Docker containers.
Additionally it invokes the tool ``catkin_test_results --all`` to output a
summary of all tests.


.. _devel_call_graph: devel_call_graph.png
