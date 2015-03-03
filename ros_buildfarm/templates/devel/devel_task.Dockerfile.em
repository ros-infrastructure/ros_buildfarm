# generated from @template_name

@(TEMPLATE(
    'snippet/from_base_image.Dockerfile.em',
    os_name=os_name,
    os_code_name=os_code_name,
    arch=arch,
))@
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

@[if os_name == 'ubuntu']@
# Add multiverse
RUN echo deb http://archive.ubuntu.com/ubuntu @os_code_name multiverse | tee -a /etc/apt/sources.list
@[else if os_name == 'debian']@
# Add contrib and non-free to debian images
RUN echo deb http://http.debian.net/debian @os_code_name contrib non-free | tee -a /etc/apt/sources.list
@[end if]@

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

@(TEMPLATE(
    'snippet/install_dependencies.Dockerfile.em',
    dependencies=dependencies,
    dependency_versions=dependency_versions,
))@

USER buildfarm
ENTRYPOINT ["sh", "-c"]
@{
if not testing:
    cmd = 'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u ' + \
        '/tmp/ros_buildfarm/scripts/devel/catkin_make_isolated_and_install.py ' + \
        '--rosdistro-name %s --clean-before' % rosdistro_name
else:
    cmd = 'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u ' + \
        '/tmp/ros_buildfarm/scripts/devel/catkin_make_isolated_and_test.py ' + \
        '--rosdistro-name %s' % rosdistro_name
if not prerelease_overlay:
    cmd += ' --workspace-root /tmp/catkin_workspace'
else:
    cmd += ' --workspace-root /tmp/catkin_workspace_overlay ' + \
        '--parent-result-space /tmp/catkin_workspace/install_isolated'
}@
CMD ["@cmd"]
