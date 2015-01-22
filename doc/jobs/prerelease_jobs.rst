*prerelease* jobs
=================

A *prerelease* job is used for check if changes in a set of repositories effect
other packages which depend on them.
It operates on two separate workspaces:

* The *underlay* workspace contains a set of source repositories containing
  changes which should be checked before a release.

* The *overlay* workspace contains a set of packages which depend on the
  packages in the underlay workspace to check for regressions in the public API
  and behavior.

The job builds the code and runs the tests of both workspaces to check for
regressions.

There are no entrypoints to generate Jenkins jobs for prereleases.
Instead it can only be run locally.


Entry points
------------

The following scripts are the entry points for *prerelease* jobs:

* **generate_prerelease_script.py** generates a *shell* script which will run
  the *prerelease* task on a local machine.

  This is the only script interpreted with Python 2 to make it easier for users
  to install ``python-ros-buildfarm`` side-by-side with other ROS Python 2
  packages.


The build process in detail
---------------------------

The underlay workspace is processed in the same way as in a
`*devel* <devel_jobs.rst#the-build-process-in-detail>`_ job.
The only difference is that the workspace can contain more than one source
repository.

The source repositories can be:

* a source repositories and version registered in the rosdistro repository
* a source repositories registered in the rosdistro repository but using a
  different version
* a custom repository (usually a fork)

For the overlay workspace only the
`*build-and-test* <devel_jobs.rst#build-and-test>`_
task from the devel job is being run.
The packages are fetched using the release repositories and versions registered
in the rosdistro repository.


Example invocation
^^^^^^^^^^^^^^^^^^

The following commands run a *prerelease* job for ROS *Indigo* for Ubuntu
*Trusty* *amd64*.
The repositories in the *underlay* workspace are: *roscpp_core* and *std_msgs*
The packages defining the *overlay* workspace are: *roscpp*

.. code:: sh

  mkdir /tmp/prerelease_job
  generate_prerelease_script.py https://raw.githubusercontent.com/ros-infrastructure/ros_buildfarm_config/master/index.yaml indigo default ubuntu trusty amd64 roscpp_core std_msgs --level 0 --pkg roscpp --output-dir /tmp/prerelease_job
  cd /tmp/prerelease_job
  ./prerelease.sh

Instead of specifying the packages in the *overlay* workspace *by name* the
script also supports passing a dependency depth (``--level N``) and / or
excluding certain packages by-name (``--exclude-pkg NAME``).

Note that using the dependency depth option might lead to a very large
*overlay* workspace which can take a significant amount of time to build.


Call individual steps manually
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The generated ``prerelease.py`` script calls several other (also generated)
scripts which can be invoked manually in the same order:

* ``prerelease_clone_underlay.py`` clones all source repositories into the
  underlay workspace.
* ``prerelease_clone_overlay.py`` computes the set of packages for the overlay
  workspace, generates a file named ``prerelease_clone_overlay_impl.py`` and
  invokes it.
  That *impl* script is then cloning the released packages into the underlay
  workspace.
* ``prerelease_build_underlay.py`` runs the *build-and-install* task as well as
  the *build-and-test* task on the underlay workspace.
  It also invokes the tool ``catkin_test_results --all`` to output a
  summary of all tests in the underlay workspace.
* ``prerelease_build_overlay.py`` runs the *build-and-test* task on the overlay
  workspace.
  It also invokes the tool ``catkin_test_results --all`` to output a
  summary of all tests in the overlay workspace.
