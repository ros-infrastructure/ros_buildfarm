# generated from @template_name

FROM @os_name:@os_code_name
MAINTAINER Dirk Thomas dthomas+buildfarm@@osrfoundation.org

VOLUME ["/var/cache/apt/archives"]

ENV DEBIAN_FRONTEND noninteractive
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8

RUN useradd -u @uid -m buildfarm

@(TEMPLATE(
    'snippet/add_distribution_repositories.Dockerfile.em',
    distribution_repository_keys=distribution_repository_keys,
    distribution_repository_urls=distribution_repository_urls,
    os_code_name=os_code_name,
    add_source=False,
))@

@(TEMPLATE(
    'snippet/add_wrapper_scripts.Dockerfile.em',
    wrapper_scripts=wrapper_scripts,
))@

# automatic invalidation once every day
RUN echo "@today_str"

@# Ubuntu before Trusty explicitly needs python3
@[if os_name == 'ubuntu' and os_code_name[0] not in ['t', 'u']]@
RUN python -u /tmp/wrapper_scripts/apt-get.py update-and-install -q -y python3
@[end if]@

RUN python3 -u /tmp/wrapper_scripts/apt-get.py update-and-install -q -y debhelper dpkg dpkg-dev git git-buildpackage python3 python3-catkin-pkg python3-rosdistro python3-yaml

USER buildfarm
ENTRYPOINT ["sh", "-c"]
@{
cmds = [
    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' +
    ' /tmp/ros_buildfarm/scripts/release/get_sources.py' +
    ' --rosdistro-index-url ' + rosdistro_index_url +
    ' ' + rosdistro_name +
    ' ' + package_name +
    ' ' + os_name +
    ' ' + os_code_name +
    ' --source-dir /tmp/sourcedeb/source',

    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' +
    ' /tmp/ros_buildfarm/scripts/release/build_sourcedeb.py' +
    ' --source-dir /tmp/sourcedeb/source',
]
}@
CMD ["@(' && '.join(cmds))"]
