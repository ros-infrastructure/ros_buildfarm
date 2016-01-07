RUN rosdep init
@[for url in custom_rosdep_urls]@
RUN (cd /etc/ros/rosdep/sources.list.d/ && wget --no-verbose -O $(basename @url ) @url )
@[end for]@
