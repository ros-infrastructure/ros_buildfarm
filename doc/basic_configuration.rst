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

First you need to either fork, clone, or copy the
`ros_buildfarm_config <https://github.com/ros-infrastructure/ros_buildfarm_config>`_
repository or create a repository containing the same configuration files.

**Important:**
Since ``ros_buildfarm_config`` files need to be accessed from within Docker images,
you **can not** use a local file system path (``file://``) to reference them.
The configuration files must be accessible via HTTP.

Then you must update the configuration files:


Disable notification of maintainers / committers
------------------------------------------------

**Disable the notification of package maintainers and committers** in order to
not send emails to maintainers and committers about the results of your custom
build farm.

The following options must be set in *all* build files::

    notifications:
      committers: false
      maintainers: false


Update administrator notification
---------------------------------

Change the email address which gets notified about any administrative jobs.

In your ``ros_buildfarm_config``'s ``index.yaml``::

  notification_emails:
  - your_email@example.com

In *all* build files::

  notifications:
    emails:
    - your_email@example.com

You need to have a `local SMTP service configured <https://github.com/ros-infrastructure/buildfarm_deployment#setup-master-for-email-delivery>`_ on your ``master`` host for email notifications.
Note that even when you remove these global email notification settings
some jobs will still send notification emails to package specific email addresses
by default unless this is disabled by configuration.


Update URLs to point to custom build farm
-----------------------------------------

Change the ``rosdistro_index_url`` in your ``ros_buildfarm_config``'s ``index.yaml`` 
to point to the ``rosdistro``'s ``index.yaml``
that defines the distro(s) that your buildfarm should build and respective caches.

This can be the official `ros/rosdistro <https://github.com/ros/rosdistro>`_'s ``index.yaml`` 
if you intend to build the default set of packages, or your personal configuration where you intend to host
``rosdistro`` (for example a GitHub fork of ``ros/rosdistro`` or your ``repo`` host)::

  rosdistro_index_url: https://raw.githubusercontent.com/ros/rosdistro/master/index.yaml

Change the Jenkins URL in your ``ros_buildfarm_config``'s 
``index.yaml`` to point to your earlier provisioned Jenkins master::

  jenkins_url: http://jenkins_hostname.example.com:8080

Change the repository URLs in your ``ros_buildfarm_config``_'s
``index.yaml`` to point to your earlier provisioned ``repo`` host::

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


Update URLs to point to required repositories
---------------------------------------------

During job execution, access to repositories which contain the necessary tools to run the ROS build farm is required.
These must be specified in your ``ros_buildfarm_config``'s ``index.yaml`` as ``prerequisites``.
You can use the official ROS repository or mirrors of it.
See the `Configuration Options <configuration_options.rst#entry-point-yaml>`_ documentation page for details.
