FROM @os_name:@os_code_name
MAINTAINER @maintainer_name @maintainer_email

VOLUME ["/var/cache/apt/archives"]

ENV DEBIAN_FRONTEND noninteractive
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8

RUN useradd -u @uid -m buildfarm

RUN mkdir /tmp/keys
@[for i, key in enumerate(distribution_repository_keys)]@
RUN echo "@('\\n'.join(key.splitlines()))" > /tmp/keys/@(i).key
RUN apt-key add /tmp/keys/@(i).key
@[end for]@
@[for url in distribution_repository_urls]@
RUN echo deb @url @os_code_name main | tee -a /etc/apt/sources.list.d/buildfarm.list
@[end for]@

@[if os_name == 'ubuntu']@
# Add multiverse
RUN echo deb http://archive.ubuntu.com/ubuntu @os_code_name multiverse | tee -a /etc/apt/sources.list
@[else if os_name == 'debian']@
# Add contrib and non-free to debian images
RUN echo deb http://http.debian.net/debian @os_code_name contrib non-free | tee -a /etc/apt/sources.list
@[end if]@

# if any dependency version has changed invalidate cache
@[for k in sorted(dependency_versions.keys())]@
RUN echo "@k: @dependency_versions[k]"
@[end for]@

# automatic invalidation once every day
@{
import datetime
today_isoformat = datetime.date.today().isoformat()
}@
RUN echo "@today_isoformat"

ADD apt-get.py /tmp/
RUN python3 -u /tmp/apt-get.py update

@[for d in dependencies]@
RUN python3 -u /tmp/apt-get.py install -q -y @d
@[end for]@

USER buildfarm
ENTRYPOINT ["sh", "-c"]
@{
if not testing:
    cmd = 'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u ' + \
        '/tmp/ros_buildfarm/scripts/devel/catkin_make_isolated_and_install.py ' + \
        '--rosdistro-name %s --workspace-root /tmp/catkin_workspace --clean-before' % rosdistro_name
else:
    cmd = 'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u ' + \
        '/tmp/ros_buildfarm/scripts/devel/catkin_make_isolated_and_test.py ' + \
        '--rosdistro-name %s --workspace-root /tmp/catkin_workspace' % rosdistro_name
}@
CMD ["@cmd"]
