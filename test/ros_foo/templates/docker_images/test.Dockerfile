# generated from templates/docker_images/test.Dockerfile.em

FROM ubuntu:trusty
MAINTAINER Dirk Thomas dthomas+buildfarm@osrfoundation.org

RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV TZ PDT+07

RUN mkdir /tmp/keys

# install bootstrap tools
RUN apt-get update && apt-get install -q -y \
    python-rosdep \
    python-rosinstall \
    python-vcstools

# bootstrap rosdep
RUN rosdep init

# install requested metapackage
RUN apt-get update && apt-get install -q -y roscpp
ENV ROS_DISTRO indigo# TODO source rosdistro setup file automatically on entry
ENTRYPOINT ["bash", "-c"]
CMD ["bash"]
