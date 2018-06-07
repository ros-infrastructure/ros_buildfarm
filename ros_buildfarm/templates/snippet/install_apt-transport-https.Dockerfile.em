@[if os_name == 'debian']@
@# workaround for https://github.com/ros-infrastructure/ros_buildfarm/pull/549
RUN for i in 1 2 3; do apt-get update && apt-get install -q -y apt-transport-https && apt-get clean && break || if [[ $i < 3 ]]; then sleep 5; else false; fi; done
@[end if]@
