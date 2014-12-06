ROS buildfarm based on Docker
=============================

The ROS buildfarm is a new implementation using
`Docker <http://www.docker.com>`_ for each step in the process.
It is based on the ROS distro specification
`REP 143 <https://github.com/ros-infrastructure/rep/pull/87>`_ and uses a
separate
`configuration for the buildfarm <https://github.com/ros-infrastructure/ros_buildfarm_config>`_.


What does it do?
----------------

The buildfarm performs various different jobs.
For each job type you will find a detailed description what they do and how
they work.

* `release jobs <jobs/release_jobs.rst>`_ generate binary package
* `devel jobs <jobs/devel_jobs.rst>`_ build and test ROS repositories
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
