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

  You need to install the Python package ``ros_buildfarm`` before being able to
  invoke the script.

  This is the only script interpreted with Python 2 to make it easier for users
  to install the Debian package ``python-ros-buildfarm`` side-by-side with
  other ROS Python 2 packages.


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
* a custom repository (e.g a fork or a repository not yet registered in the ROS
  distribution)

For the overlay workspace only the
`*build-and-test* <devel_jobs.rst#build-and-test>`_ task from the devel job is
being run.
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
  generate_prerelease_script.py https://raw.githubusercontent.com/ros-infrastructure/ros_buildfarm_config/production/index.yaml indigo default ubuntu trusty amd64 roscpp_core std_msgs --pkg roscpp --output-dir /tmp/prerelease_job
  cd /tmp/prerelease_job
  ./prerelease.sh

By passing the optional command line argument `--custom-branch` a custom branch
or tag can be selected for each repository.
For each repository the repository name followed by a colon, followed by the
custom branch or tag name need to be passed, e.g.:

.. code:: sh

  generate_prerelease_script.py ... roscpp_core std_msgs ... --custom-branch \
    roscpp_core:mybranch std_msgs:mytag

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
  It also invokes the tool ``catkin_test_results --all`` /
  ``colcon test-result --all`` to output a summary of all tests in the underlay
  workspace.
* ``prerelease_build_overlay.py`` runs the *build-and-test* task on the overlay
  workspace.
  It also invokes the tool ``catkin_test_results --all`` /
  ``colcon test-result --all`` to output a summary of all tests in the overlay
  workspace.

Run the *prerelease* job on Travis
----------------------------------

Since it is easy to run a *prerelease* job locally it can also be run on Travis to either test every commit or pull request.
The setup and invocation is the same as locally.
The `.travis.yml <https://github.com/ros-infrastructure/ros_buildfarm/blob/master/.travis.yml>`_ file of the *ros_buildfarm* repository is a good starting point.

Run for "custom" repositories
-----------------------------

Most job types require that the tested repository is being listed in a ROS distribution file.
For the *prerelease* job that is not necessary.
Any repository containing ROS packages can be processed by this job.

Since the ROS distribution doesn't know about the repositories several pieces
of information have to be passed using the command line argument
`--custom-repo`.
The following parts are all separated by colons: the repository name, the
repository type, the repository URL, the branch or tag name, e.g.:

.. code:: sh

  generate_prerelease_script.py ... --custom-repo \
    my_repo_name:git:https://github.com/dirk-thomas/roscpp_core.git:mybranch

If the ROS packages in a repository depend on other packages not available in
the ROS distribution the repositories containing them need to be listed too.
The *underlay* workspace will then contain all "custom" repositories.

As an alternative to specify all custom repos as command line arguments it is possible to manually populate the underlay (and/or overlay) workspace.
The following commands are all it takes to run a prerelease job for a custom repository not mentioned in any ROS distribution:

.. code:: sh

  mkdir /tmp/prerelease && cd /tmp/prerelease
  git clone -b dummy_package https://github.com/ros-infrastructure/ros_buildfarm ws/src/ros_buildfarm
  generate_prerelease_script.py https://raw.githubusercontent.com/ros-infrastructure/ros_buildfarm_config/production/index.yaml kinetic default ubuntu xenial amd64 --output-dir .
  # the argument -y suppresses the question if you want to continue with content already present in the workspace
  ./prerelease.sh -y

The git clone command is just an example.
It can be substituted with any other commands to populate the workspaces (e.g. `wstool`, `vcstool`).
