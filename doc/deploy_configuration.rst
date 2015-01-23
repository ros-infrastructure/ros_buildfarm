Deploy ROS build farm configuration
===================================

The initial deployment consists of three steps:

* generating the administrative Jenkins jobs
* triggering a few jobs to perform necessary initialization steps
* generate all release / devel / doc jobs

Before being able to run the deployment script you must
`setup your environment <environment.rst>`_.


Generate the administrative Jenkins jobs
----------------------------------------

To generate the administrative jobs invoke the following commands pointing to
the URL of your build farm configuration (substitute ``YOUR_FORK``
accordingly)::

  generate_all_jobs.py https://raw.githubusercontent.com/YOUR_FORK/ros_buildfarm_config/master/index.yaml

Instead of generating all jobs at once there are similar scripts to only deploy
the jobs of a specific type.


Trigger jobs to perform initialization
--------------------------------------

Log in as the *admin* user to the Jenkins master using your password defined in
the configuration.
All administrative jobs can be found in the *Manage* view.


Import packages
^^^^^^^^^^^^^^^

Trigger the job ``import_upstream`` to get all the required bootstrap packages
into the repository.


rosdistro cache
^^^^^^^^^^^^^^^

You can disable the following jobs if you are not using a forked rosdistro
database.

Otherwise trigger the ``*_rosdistro-cache`` job for each ROS distribution and
verify that it uploaded the generated cache files successfully to your ``repo``
machine:

  http://repo_hostname.example.com/rosdistro_cache/


Generate devel / release / doc jobs
-----------------------------------

The job generation for specific packages / repositories happens automatically
(e.g. once a day) to make sure to create jobs for newly added packages and
repositories and remove obsolete jobs for removed packages and repositories.
But you might want to trigger all ``*_reconfigure-jobs`` manually to ensure
that they succeed and generate the desired jobs.

Note that the job reconfiguration takes a significant amount of time (e.g. for
Indigo on the ROS build farm roughly 45 minutes).
