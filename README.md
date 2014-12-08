# ROS buildfarm based on Docker

The ROS buildfarm is a new implementation using
[Docker](http://www.docker.com) for each step in the process.
It is based on the ROS distro specification
[REP 143](http://www.ros.org/reps/rep-0143.html) and uses a
separate
[configuration for the buildfarm](https://github.com/ros-infrastructure/ros_buildfarm_config).

This repository contains the scripts and templates to generate Jenkins jobs or
alternatively shell scripts to run jobs locally.
Please look in the [doc](doc/index.rst) folder for more information.
