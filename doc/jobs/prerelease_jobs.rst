*prerelease* jobs
=================

A *prerelease* job is used for check if changes in a set of repositories effect
other packages which depend on them.
It operates on two separate workspaces:

* the *underlay* workspace contains a set of source repositories containing
  changes which should be checked before a release

* the *overlay* workspace contains a set of packages which depend on the
  packages in the underlay workspace to check for regressions in the public API
  and behavior

The job builds the code and runs the tests to check for regressions.

There are no entrypoints to generate Jenkins jobs for prereleases.
Instead it can only be run locally.


Entry points
------------

The following scripts are the entry points for *prerelease* jobs:

* ``generate_prerelease_script.py`` generates a *shell* script which will run
  the prerelease on a local machine.


The build process in detail
---------------------------

The underlay workspace is processed in the same way as in a *devel* job.
The only difference is that the workspace can contain more than one source
repository.

The source repositories can be:

* a source repositories and version registered in the rosdistro repository
* a source repositories registered in the rosdistro repository but using a
  different version
* a custom repository (usually a fork)

For the overlay workspace only the *build-and-test* task from the devel job is
being run.
The packages are fetched using the release repositories and versions registered
in the rosdistro repository.


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
