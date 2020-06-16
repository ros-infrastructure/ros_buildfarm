# ROS build farm based on Docker

This repository contains the scripts and templates to generate Jenkins jobs or
alternatively shell scripts to run jobs locally.
Please look in the [doc](doc/index.rst) folder for more information about how
to invoke the job generation and an explanation of the different job types.

The ROS build farm is using [Docker](http://www.docker.com) for each step in
the process.
It is based on the ROS distro specification
[REP 143](http://www.ros.org/reps/rep-0143.html) and uses a separate repository
to configure the jobs being generated (e.g.
[ros-infrastructure/ros_buildfarm_config](https://github.com/ros-infrastructure/ros_buildfarm_config)).

If you are going to use any of the provided infrastructure please consider
watching the [buildfarm Discourse category](https://discourse.ros.org/c/buildfarm)
in order to receive notifications e.g. about any upcoming changes.

For quick reference to run scripts:

 ## Check Sync Criteria

    ./scripts/release/check_sync_criteria.py https://raw.githubusercontent.com/ros-infrastructure/ros_buildfarm_config/production/index.yaml melodic default ubuntu bionic amd64

## Audit rosdistro

    ./scripts/release/audit_rosdistro.py --cache-dir /tmp/rosdistrocache https://raw.githubusercontent.com/ros-infrastructure/ros_buildfarm_config/production/index.yaml noetic
