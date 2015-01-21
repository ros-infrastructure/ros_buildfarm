ROS build farm based on Docker
==============================

For an overview about the ROS build farm including how to deploy the necessary
machine see the `ROS wiki page <http://wiki.ros.org/buildfarm>`_.


Job types
---------

The ROS build farm performs several different jobs.
For each job type you will find a detailed description what they do and how
they work.

* `release jobs <jobs/release_jobs.rst>`_ generate binary packages

* `devel jobs <jobs/devel_jobs.rst>`_ build and test ROS repositories

* doc jobs (to be done) generate the API documentation of packages

* `miscellaneous jobs <jobs/miscellaneous_jobs.rst>`_ perform maintenance tasks
  and generate informational data to visualize the status of the build farm and
  its generated artifacts


Configuration
-------------

The ROS build farm needs to be configured to specify custom URLs, credentials,
and which jobs should be generated for which platforms and architectures.

The configuration is stored in a separate repository (e.g.
`ros_buildfarm_config <https://github.com/ros-infrastructure/ros_buildfarm_config>`_
for the official ROS build farm.

Each use case below describes the configuration option most commonly used.
But for reference there is also a list of
`all configuration options <configuration.rst>`_ available.


Generate the Jenkins jobs
-------------------------

In order to setup a custom build farm you will need to follow the
`general process <general_process.rst>`_ instructions.
They describe how to setup your environment to generate the administrative
Jenkins jobs as well as which jobs need to be triggered to generate all other
Jenkins jobs.

Please continue reading all use cases before starting the process to figure
out which fits your scenario since they build on-top of each other.


Common use cases
----------------

Below are some common use cases which describe specifics about how to customize.

* run the `same build farm <how_to_deploy_buildfarm.rst>`_ locally which:

  * uses the same rosdistro database
  * the unmodified ROS build farm code
  * the unmodified configuration

* run a `customized build farm <how_to_deploy_customized_buildfarm.rst>`_ which
  uses:

  * a modified configuration to build:

    * only a subset of packages
    * a different set of targets

  * a modified codebase to perform the tasks differently

* run a `build farm with a forked rosdistro database <how_to_fork_rosdistro_database.rst>`_

* run a `build farm with custom packages <how_to_build_and_release_custom_packages.rst>`_


Run jobs locally
----------------

Some of the job types can be easily run locally.
This allows to reproduce the behavior of the build farm locally, eases
debugging, and shortens the round-trip time for testing.

* `release jobs#run-the-release-job-locally <jobs/release_jobs.rst#run-the-release-job-locally>`_
  generate binary packages

* `devel jobs#run-the-devel-job-locally <jobs/devel_jobs.rst#run-the-devel-job-locally>`_
  build and test ROS repositories

Another job type can be used locally which is not offered on the build farm.

* `prerelease jobs <jobs/prerelease_jobs.rst>`_ build and test ROS repositories
  as well as build and test released ROS packages depending on them
