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

* Change the repository URLs to point to your earlier provisioned ``repo``
  host::

    index.yaml:
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


Deploy your configuration to jenkins
------------------------------------

As documented in the `general process documentation<general_process.rst>`_.


Run administrative tasks
------------------------

As documented in the `general process documentation<general_process.rst>`_.
