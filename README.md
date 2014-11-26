ros_buildfarm
=============

Scripts and templates to generate Jenkins jobs or alternatively scripts to run
jobs locally. The [doc](doc/index.rst) folder contains more information.

You will need a set of configuration files, e.g. from the
[ros_buildfarm_config](https://github.com/ros-infrastructure/ros_buildfarm_config)
repository.

To provision a Jenkins master, multiple slaves and additional services like an
apt repository and a webserver to host the generated documention you might want
to use the
[buildfarm_deployment](https://github.com/ros-infrastructure/buildfarm_deployment)

You will need the following dependencies:

* a forked version of [jenkinsapi](https://github.com/dirk-thomas/jenkinsapi/tree/feature/config_view)
* a forked version of [rosdistro](https://github.com/ros-infrastructure/rosdistro/tree/rep143)
