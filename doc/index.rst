ROS buildfarm based on Docker
=============================

The ROS buildfarm is a new implementation using
`Docker <http://www.docker.com>`_ for each step in the process.
It is based on the ROS distro specification
`REP 143 <http://www.ros.org/reps/rep-0143.html>`_ and uses a
separate
`configuration for the buildfarm <https://github.com/ros-infrastructure/ros_buildfarm_config>`_.


What does it do?
----------------

The buildfarm performs various different jobs.
For each job type you will find a detailed description what they do and how
they work.

* `release jobs <jobs/release_jobs.rst>`_ generate binary package
* `devel jobs <jobs/devel_jobs.rst>`_ build and test ROS repositories
* `prerelease jobs <jobs/prerelease_jobs.rst>`_ build and test ROS repositories
  as well as build and test released ROS packages depending on them
* doc jobs (to be done) generate the API documentation of packages
* `miscellaneous jobs <jobs/miscellaneous_jobs.rst>`_ perform maintenance tasks
  and generate informational data to visualize the status of the buildfarm and
  its generated artifacts


How to deploy a ROS buildfarm
-----------------------------

There are various different use cases for running your own ROS buildfarm.
The most common ones are listed below.

If you want to deploy your own buildfarm please read all how-to's before the
one which fits your scenario since they build on-top of each other.

Please make sure that you have the latest released version of the ROS Python
tools installed, e.g. rosdistro >= 0.4.0, rosdep >= 0.11.0, bloom >= 0.5.15.

To run a deployment you will need to follow this `general process <general_process.rst>`_


Example Use Cases
-----------------

Below are some common use cases which describe specifics about how to customize.

* run the `same buildfarm <how_to_deploy_buildfarm.rst>`_ locally which:

  * uses the same rosdistro database as well as
  * the unmodified ROS buildfarm code

* run a `customized buildfarm <how_to_deploy_customized_buildfarm.rst>`_ which
  uses:

  * a modified configuration to build:

    * only a subset of packages
    * a different set of targets

  * a modified codebase to perform the tasks differently

* run a `buildfarm with a forked rosdistro database <how_to_fork_rosdistro_database.rst>`_

* run a `buildfarm with custom packages <how_to_build_and_release_custom_packages.rst>`_
