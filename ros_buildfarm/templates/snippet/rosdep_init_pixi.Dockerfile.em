# rosdep 0.27.0 ignores ROS_ETC_DIR and uses /etc/ros on the current drive
RUN pixi run rosdep init
@[for url in custom_rosdep_urls]@
ADD @url C:/etc/ros/rosdep/sources.list.d/
@[end for]@
