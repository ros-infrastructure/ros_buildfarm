@[if os_name == 'debian' and os_code_name == 'jessie']@
@# workaround for https://github.com/ros-infrastructure/ros_buildfarm/issues/369
RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y apt-src
@[end if]@
