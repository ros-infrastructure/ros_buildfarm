# test generated from @template_name

@(TEMPLATE(
    'snippet/from_base_image.Dockerfile.em',
    template_packages=template_packages,
    os_name=os_name,
    os_code_name=os_code_name,
    arch=arch,
    base_image=base_image,
))@
MAINTAINER Dirk Thomas dthomas+buildfarm@@osrfoundation.org

# setup environment
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV TZ PDT+07

# install packages
RUN apt-get update && apt-get install -q -y \
    @(' \\\n    '.join(packages))@


# setup keys
RUN wget https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -O - | apt-key add -

# setup sources.list
RUN echo "deb http://packages.ros.org/ros/@os_name @os_code_name main" > /etc/apt/sources.list.d/ros-latest.list

# install bootstrap tools
RUN apt-get update && apt-get install --no-install-recommends -q -y \
    python-rosdep \
    python-rosinstall \
    python-vcstools

# bootstrap rosdep
RUN rosdep init \
    && rosdep update

# install ros packages
RUN apt-get update && apt-get install -q -y \
    @(' \\\n    '.join(ros_packages))@


# setup .bashrc for ROS
ENV ROS_DISTRO @rosdistro_name
RUN echo "source /opt/ros/@rosdistro_name/setup.bash" >> ~/.bashrc

ENTRYPOINT ["bash", "-c"]
@{
cmds = [
'bash',
]
}@
CMD ["@(' && '.join(cmds))"]
