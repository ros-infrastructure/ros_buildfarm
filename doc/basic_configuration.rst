How to configure an "identical" ROS build farm?
===============================================

This how-to will describe the configuration options necessary for a ROS build
farm which behaves like the official ROS build farm.
The resulting build farm will perform the following tasks:

* generate release packages
* run continuous integration on commits and pull requests
* generate API documentation

Please see the `index <index.rst>`_ page for further instructions about
provisioning the build farm machines and how to apply the ROS build farm
configuration to generate the necessary Jobs on the Jenkins master.


Create / fork configuration repository
--------------------------------------

First you need to either fork the
`ros_buildfarm_config <https://github.com/ros-infrastructure/ros_buildfarm_config>`_
repository or create a repository containing the same configuration files.

Then you must update the configuration files:


Disable notification of maintainers / committers
------------------------------------------------

**Disable the notification of package maintainers and committers** in order to
not send emails to maintainers and committers about the results of your custom
build farm.

The following options must be set in *all* build files::

    notifications:
      committers: false
    maintainers
      committers: false


Update administrator notification
---------------------------------

Change the email address which gets notified about any administrative jobs.

In the entry point yaml::

  notification_emails:
  - your_email@example.com

In *all* build files::

  notifications:
    emails:
    - your_email@example.com


Update URLs to point to custom build farm
-----------------------------------------

Change the Jenkins URL in the entry point yaml to point to your earlier
provisioned Jenkins master::

  jenkins_url: http://jenkins_hostname.example.com:8080

Change the repository URLs in the entry point yaml to point to your earlier
provisioned ``repo`` host::

  status_page_repositories:
    CUSTOM_NAME:
    - http://repo_hostname.example.com/ubuntu/building
    - http://repo_hostname.example.com/ubuntu/testing
    - http://repo_hostname.example.com/ubuntu/main

Change the repository URLS and keys to point to your earlier provisioned *repo*
machine.

The *release* build files usually points to the ``building`` repository::

  repositories:
    urls:
    - http://repo_hostname.example.com/ubuntu/building
    keys
    - |
      ...
      ...
  target_repository: http://repo_hostname.example.com/ubuntu/building

The *source* / *doc* build files usually point to the ``testing``
repository::

  repositories:
    urls:
    - http://repo_hostname.example.com/ubuntu/testing
    keys
    - |
      ...
      ...

You can extract the repository PGP key from the ``buildfarm_deployment``
configuration.
