How to deploy the same buildfarm locally?
=========================================

This how-to will make you setup a ROS buildfarm which is identical to the
official ROS buildfarm.
It will:

* generate release packages
* run continuous integration on commits and pull requests
* generate API documentation


Provision the build farm machines
---------------------------------

To provision the build farm machines please follow the documentation in the
`buildfarm_deployment <https://github.com/ros-infrastructure/buildfarm_deployment>`_
repository.


Configure your buildfarm
------------------------

First you need to either fork the
`ros_buildfarm_config <https://github.com/ros-infrastructure/ros_buildfarm_config>`_
repository or create a repository containing these configuration files.

Then you can update the configuration files:

* **Disable the notification of package maintainers and committers** in order to
  not send emails to everybody about the results of your custom buildfarm::

    all build files:
      notifications:
        committers: false
       maintainers
        committers: false

* Change the Jenkins URL to point to your earlier provisioned Jenkins master::

    index.yaml:
      jenkins_url: http://jenkins_hostname.example.com:8080

* Change the repository URLs  to point to your earlier provisioned ``repo``
  host::

    status_page_repositories:
      CUSTOM_NAME:
      - http://repo_hostname.example.com/ubuntu/building
      - http://repo_hostname.example.com/ubuntu/testing
      - http://repo_hostname.example.com/ubuntu/main

* Change the email address which gets notified about any administrative
  events::

    index.yaml:
      notification_emails:
      - ...

    all build files:
      notifications:
        emails:
        - ...

* Change the repository URLS and keys to point to your earlier provisioned
  *repo* machine.

  The release build file usually points to the ``building`` repository::

    release build files:
      repositories:
        urls:
        - http://repo_hostname.example.com/ubuntu/building
        keys
        - |
          ...
          ...
      target_repository: http://repo_hostname.example.com/ubuntu/building

  The source / doc build files usually point to the ``testing`` repository::

    release build files:
      repositories:
        urls:
        - http://repo_hostname.example.com/ubuntu/testing
        keys
        - |
          ...
          ...

  You can extract the repository key from the ``buildfarm_deployment``
  configuration.


Setup your machine to configure Jenkins
---------------------------------------

For generating Jenkins jobs you need the following software:

* Python 3
* Python 3 package ``empy``
* a checkout of the `ros_buildfarm <https://github.com/ros-infrastructure/ros_buildfarm) repository>`_
* a forked version of `jenkinsapi <https://github.com/dirk-thomas/jenkinsapi/tree/feature/config_view>`_
* a forked version of `rosdistro <https://github.com/ros-infrastructure/rosdistro/tree/rep143>`_

E.g. using the following commands on Ubuntu Trusty::

    sudo apt-get update && sudo apt-get install python3 python3-all python3-pip

    mkdir /tmp/deploy_ros_buildfarm
    cd /tmp/deploy_ros_buildfarm
    pyvenv-3.4 venv
    . venv/bin/activate
    pip3 install empy
    pip3 install git+git://github.com/dirk-thomas/jenkinsapi.git@feature/config_view
    pip3 install git+git://github.com/ros-infrastructure/rosdistro.git@rep143

    git clone https://github.com/ros-infrastructure/ros_buildfarm.git
    cd ros_buildfarm
    export PYTHONPATH=`pwd`:$PYTHONPATH

Create the file ``~/.buildfarm/jenkins.ini`` containing your credentials to log
in to the Jenkins master, e.g.::

    [jenkins_hostname.example.com]
    username=admin
    password=changeme

For now there is a helper script in
`this <https://github.com/tfoote/buildfarm_inprogress_helpers>`_ repo which
will set up this environment for you inside a docker instance.


Generate the Jenkins jobs
-------------------------

To generate the administrative jobs invoke the following commands pointing to
the URL of your buildfarm configuration::

    /tmp/deploy_ros_buildfarm/ros_buildfarm/scripts/generate_all_jobs.py https://raw.githubusercontent.com/YOUR_FORK/ros_buildfarm_config/master/index.yaml


Run administrative tasks
------------------------

Log in as the *admin* user to the Jenkins master.


Import packages
^^^^^^^^^^^^^^^

Run the following jobs from the *Manage* view:

* ``import_upstream`` to get all the required bootstrap packages into the
  repository


rosdistro cache
^^^^^^^^^^^^^^^

You can disable the following jobs if you are not using a forked rosdistro
database:

* ``*_rosdistro-cache``

Otherwise trigger each ``rosdistro-cache`` job once and verify that it uploaded
the generated cache files successfully to:
http://repo_hostname.example.com/rosdistro_cache/


Generate devel / release / doc jobs
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Run the following jobs from the *Manage* view:

* ``*__reconfigure-jobs`` to generate all the jobs


Generated jobs
--------------

All management related jobs are shown in the ``Manage`` view in Jenkins.

The reconfiguration jobs are automatically retriggered (some frequently, others
daily) to make sure to create jobs for newly added packages and repositories
and remove obsolete jobs for removed packages and repositories.

For each build file a corresponding view contains all jobs generated by that
build file.
Each job type uses a different triggering mechanisms.
For details please see the job specific documentation pages referenced from the
index page.


Ongoing operations
------------------

You might want to check:

* the output of the ``dashboard`` job to get an overview about the status of all
  jobs

* the generated status pages http://REPO_HOSTNAME/status_page/ to see the
  progress of the generated packages


Manually sync packages
^^^^^^^^^^^^^^^^^^^^^^

Whenever you want to sync the current state of packages from the ``testing`` to
the ``main`` repository you must manually invoke the corresponding
``sync-packages-to-main`` job.


Users using your custom binary packages
---------------------------------------

The users must replace the original ROS repository in their APY sources files
with the URL of your ``repo`` host in order to use your binary packages.
