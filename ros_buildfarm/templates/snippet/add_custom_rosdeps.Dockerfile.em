RUN mkdir -p /etc/ros/rosdep/sources.list.d

@[for url in custom_rosdep_urls]@
RUN (cd /etc/ros/rosdep/sources.list.d/ && wget --progress=dot @url )
@[end for]@
@[if not custom_rosdep_urls]@
RUN rosdep init
@[end if]@
