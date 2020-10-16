ROS build farm based on Docker
==============================

For an overview about the ROS build farm including how to deploy the necessary
machines see the `ROS wiki page <http://wiki.ros.org/buildfarm>`_.


Job types
---------

The ROS build farm performs several different jobs.
For each job type you will find a detailed description what they do and how
they work.

* `release jobs <jobs/release_jobs.rst>`_ generate binary packages

* `devel jobs <jobs/devel_jobs.rst>`_ build and test ROS packages within a single repository

* `CI jobs <jobs/ci_jobs.rst>`_ build and test ROS packages across repositories with the option of using artifacts from other CI jobs to speed up the build

* `doc jobs <jobs/doc_jobs.rst>`_ generate the API documentation of packages
  and extract information from the manifests

* `miscellaneous jobs <jobs/miscellaneous_jobs.rst>`_ perform maintenance tasks
  and generate informational data to visualize the status of the build farm and
  its generated artifacts


Configuration
-------------

The configuration is stored in a separate repository (e.g.
`ros_buildfarm_config <https://github.com/ros-infrastructure/ros_buildfarm_config>`_
for the official ROS build farm).

Every ROS build farm requires a custom configuration to specify URLs,
credentials, and notification settings.
Please see the list of the
`basic configuration options <basic_configuration.rst>`_ which need to be
modified.

Beside the use case focused descriptions below a reference listing
`all configuration options <configuration_options.rst>`_ is available.


Customize "what" to build
^^^^^^^^^^^^^^^^^^^^^^^^^

The configuration options to change:

* which packages / repositories to process
* which platforms and architectures to target

are described `here <configure_customized_buildfarm.rst>`_.


Use a custom rosdistro database
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

In the case when you want to add packages and repositories to the rosdistro
database and / or modify the version number of released packages (e.g. lock the
version number of certain packages) you must maintain your own rosdistro
database.

Please see the documentation about using a
`custom rosdistro database <custom_rosdistro.rst>`_ for the necessary
configuration options and administrative tasks.


Dealing with large and/or duplicated configuration elements
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The YAML loader used to load the configuration implements a special constructor
used to load the YAML content from another file.
This mechanism can be used to include configuration elements from a separate
file as if it were embedded into another file.
The special directive takes a single URL argument, which may either be relative
to the current URL or absolute.

For example: ``large_block: !include other_file.yaml``


Generate the Jenkins jobs
-------------------------

After creating a custom configuration repository you can
`deploy the configuration <deploy_configuration.rst>`_ which includes:

* generating the administrative Jenkins jobs
* triggering a few jobs to perform necessary initialization steps
* generate all release / devel / doc jobs

After the initial deployment the administrator should continuously
`monitor the build farm <ongoing_operations.rst>`_ and perform some manual task
in regular intervals.


Run jobs locally
----------------

Some of the job types can be easily run locally.
This allows to reproduce the behavior of the build farm locally, eases
debugging, and shortens the round-trip time for testing.
It also means that you can run any of these jobs anywhere, e.g. on Travis.

* `release jobs#run-the-release-job-locally <jobs/release_jobs.rst#run-the-release-job-locally>`_
  generate binary packages

* `devel jobs#run-the-devel-job-locally <jobs/devel_jobs.rst#run-the-devel-job-locally>`_
  build and test ROS repositories

  * `devel jobs#run-the-devel-job-on-travis <jobs/devel_jobs.rst#run-the-devel-job-on-travis>`_
    build and test ROS repositories using Travis

* `doc jobs#run-the-doc-job-locally <jobs/doc_jobs.rst#run-the-doc-job-locally>`_
  generate the documentation for ROS repositories

Another job type can be used locally which is not offered on the build farm.

* `prerelease jobs <jobs/prerelease_jobs.rst>`_ build and test ROS
  repositories as well as build and test released ROS packages depending on them

Optimization
------------

If you are going to be running one or more jobs on any machine we recommend `using squid-in-a-can <https://github.com/jpetazzo/squid-in-a-can>`_ to cache downloads.
It can greatly speed up download times and saves a lot of bandwidth.
It's used by all our developers as well as on all the build machines.
