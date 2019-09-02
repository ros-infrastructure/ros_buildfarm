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

First you need to either fork or clone the
`ros_buildfarm_config <https://github.com/ros-infrastructure/ros_buildfarm_config>`_
repository or create a repository containing the same configuration files.

**Important:**
Since ``ros_buildfarm_config`` files need to be accessed from within docker images,
you **can not** use a local file system path (``file:/``) to reference them.
You have to provide an http server where the configuration files can be accessed.
(Note that on the build farm master, Jenkins usually occupies the standard port 80).


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

In `ros-infrastructure/ros_buildfarm_config <https://github.com/ros-infrastructure/ros_buildfarm_config>`_'s `index.yaml`::

  notification_emails:
  - your_email@example.com

In *all* build files::

  notifications:
    emails:
    - your_email@example.com

Note that you need to have a local smtp service configured for email notifications.

If you do not require email notifications, remove the configuration line entries.


Update URLs to point to custom build farm
-----------------------------------------

Change the ``rosdistro_index_url`` in the `ros-infrastructure/ros_buildfarm_config <https://github.com/ros-infrastructure/ros_buildfarm_config>`_'s 
``index.yaml`` to point to the ``rosdistro`` repository that defines the distro(s) that your buildfarm should build.

**Important:** Note that this the `rosdistro <https://github.com/ros/rosdistro>`_'s ``index.yaml``
(which points to the files that define which packages are included in the distro and respective caches),
and **not** the ``index.yaml`` in ``ros_buildfarm_config`` which you are editing.

This will usually be on the provisioned ``repo`` host, but can be the official `ros/rosdistro <https://github.com/ros/rosdistro>`_'s ``index.yaml`` if you intend to build the default set of packages.

  rosdistro_index_url: http://repo_hostname.example.com/rosdistro/index.yaml

Change the Jenkins URL in the `ros-infrastructure/ros_buildfarm_config <https://github.com/ros-infrastructure/ros_buildfarm_config>`_'s 
``index.yaml`` to point to your earlier provisioned Jenkins master::

  jenkins_url: http://jenkins_hostname.example.com:8080

Change the repository URLs in the `ros-infrastructure/ros_buildfarm_config <https://github.com/ros-infrastructure/ros_buildfarm_config>`_'s
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


Update URLs to point to required build tool repositories
--------------------------------------------------------

During job execution, access to repositories which contain the necessary tools to run the ROS build farm is required.
These can be main ROS repository or mirrors of it.
Note that the number of ``debian_repositories`` and ``debian_repository_keys`` must match, as well as the order in which they're specified.
The keys can usually be found on the repository (for example: http://packages.ros.org/ros.asc )

  prerequisites:
    debian_repositories:
    - http://packages.ros.org/ros/ubuntu
    debian_repository_keys:
    - |
      -----BEGIN PGP PUBLIC KEY BLOCK-----
      Version: GnuPG v1
      
      mQINBFzvJpYBEADY8l1YvO7iYW5gUESyzsTGnMvVUmlV3XarBaJz9bGRmgPXh7jc
      VFrQhE0L/HV7LOfoLI9H2GWYyHBqN5ERBlcA8XxG3ZvX7t9nAZPQT2Xxe3GT3tro
      u5oCR+SyHN9xPnUwDuqUSvJ2eqMYb9B/Hph3OmtjG30jSNq9kOF5bBTk1hOTGPH4
      K/AY0jzT6OpHfXU6ytlFsI47ZKsnTUhipGsKucQ1CXlyirndZ3V3k70YaooZ55rG
      aIoAWlx2H0J7sAHmqS29N9jV9mo135d+d+TdLBXI0PXtiHzE9IPaX+ctdSUrPnp+
      TwR99lxglpIG6hLuvOMAaxiqFBB/Jf3XJ8OBakfS6nHrWH2WqQxRbiITl0irkQoz
      pwNEF2Bv0+Jvs1UFEdVGz5a8xexQHst/RmKrtHLct3iOCvBNqoAQRbvWvBhPjO/p
      V5cYeUljZ5wpHyFkaEViClaVWqa6PIsyLqmyjsruPCWlURLsQoQxABcL8bwxX7UT
      hM6CtH6tGlYZ85RIzRifIm2oudzV5l+8oRgFr9yVcwyOFT6JCioqkwldW52P1pk/
      /SnuexC6LYqqDuHUs5NnokzzpfS6QaWfTY5P5tz4KHJfsjDIktly3mKVfY0fSPVV
      okdGpcUzvz2hq1fqjxB6MlB/1vtk0bImfcsoxBmF7H+4E9ZN1sX/tSb0KQARAQAB
      tCZPcGVuIFJvYm90aWNzIDxpbmZvQG9zcmZvdW5kYXRpb24ub3JnPokCVAQTAQoA
      PhYhBMHPbjHmut6IaLFytPQu1vurF8ZUBQJc7yaWAhsDBQkDwmcABQsJCAcCBhUK
      CQgLAgQWAgMBAh4BAheAAAoJEPQu1vurF8ZUkhIP/RbZY1ErvCEUy8iLJm9aSpLQ
      nDZl5xILOxyZlzpg+Ml5bb0EkQDr92foCgcvLeANKARNCaGLyNIWkuyDovPV0xZJ
      rEy0kgBrDNb3++NmdI/+GA92pkedMXXioQvqdsxUagXAIB/sNGByJEhs37F05AnF
      vZbjUhceq3xTlvAMcrBWrgB4NwBivZY6IgLvl/CRQpVYwANShIQdbvHvZSxRonWh
      NXr6v/Wcf8rsp7g2VqJ2N2AcWT84aa9BLQ3Oe/SgrNx4QEhA1y7rc3oaqPVu5ZXO
      K+4O14JrpbEZ3Xs9YEjrcOuEDEpYktA8qqUDTdFyZrxb9S6BquUKrA6jZgT913kj
      J4e7YAZobC4rH0w4u0PrqDgYOkXA9Mo7L601/7ZaDJob80UcK+Z12ZSw73IgBix6
      DiJVfXuWkk5PM2zsFn6UOQXUNlZlDAOj5NC01V0fJ8P0v6GO9YOSSQx0j5UtkUbR
      fp/4W7uCPFvwAatWEHJhlM3sQNiMNStJFegr56xQu1a/cbJH7GdbseMhG/f0BaKQ
      qXCI3ffB5y5AOLc9Hw7PYiTFQsuY1ePRhE+J9mejgWRZxkjAH/FlAubqXkDgterC
      h+sLkzGf+my2IbsMCuc+3aeNMJ5Ej/vlXefCH/MpPWAHCqpQhe2DET/jRSaM53US
      AHNx8kw4MPUkxExgI7Sd
      =4Ofr
      -----END PGP PUBLIC KEY BLOCK-----

