# generated from @template_name

@(TEMPLATE(
    'snippet/from_base_image.Dockerfile.em',
    os_name=os_name,
    os_code_name=os_code_name,
    arch=arch,
))@

VOLUME ["/var/cache/apt/archives"]

ENV DEBIAN_FRONTEND noninteractive

@(TEMPLATE(
    'snippet/old_release_set.Dockerfile.em',
    os_name=os_name,
    os_code_name=os_code_name,
))@

@(TEMPLATE(
    'snippet/setup_locale.Dockerfile.em',
    timezone=timezone,
))@

RUN useradd -u @uid -m buildfarm

@(TEMPLATE(
    'snippet/add_distribution_repositories.Dockerfile.em',
    distribution_repository_keys=distribution_repository_keys,
    distribution_repository_urls=distribution_repository_urls,
    os_name=os_name,
    os_code_name=os_code_name,
    add_source=False,
))@

@(TEMPLATE(
    'snippet/add_additional_repositories.Dockerfile.em',
    os_name=os_name,
    os_code_name=os_code_name,
    arch=arch,
))@

@(TEMPLATE(
    'snippet/add_wrapper_scripts.Dockerfile.em',
    wrapper_scripts=wrapper_scripts,
))@

# automatic invalidation once every day
RUN echo "@today_str"

@(TEMPLATE(
    'snippet/install_python3.Dockerfile.em',
    os_name=os_name,
    os_code_name=os_code_name,
))@

@[if build_tool == 'colcon']@
RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y python3-pip
@# colcon-core.package_identification.python needs at least version 30.3.0
RUN pip3 install -U setuptools
@[end if]@
@[if ros_version == 2]@
RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y ros-@(rosdistro_name)-ros-workspace
@[end if]@
RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y ccache

@(TEMPLATE(
    'snippet/set_environment_variables.Dockerfile.em',
    environment_variables=build_environment_variables,
))@

@(TEMPLATE(
    'snippet/install_dependencies.Dockerfile.em',
    dependencies=dependencies,
    dependency_versions=dependency_versions,
))@

@(TEMPLATE(
    'snippet/install_dependencies_from_file.Dockerfile.em',
    install_lists=install_lists,
))@

USER buildfarm
ENTRYPOINT ["sh", "-c"]
@{
cmd = \
    'PATH=/usr/lib/ccache:$PATH' + \
    ' PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u'
if not testing:
    cmd += \
        ' /tmp/ros_buildfarm/scripts/devel/build_and_install.py' + \
        ' --rosdistro-name %s --clean-before' % rosdistro_name
else:
    cmd += \
        ' /tmp/ros_buildfarm/scripts/devel/build_and_test.py' + \
        ' --rosdistro-name %s' % rosdistro_name
cmd += ' --build-tool ' + build_tool
if not prerelease_overlay:
    cmd += \
        ' --workspace-root /tmp/ws'
else:
    parent_result_spaces = [
        # also specify /opt/ros in case the install location has no setup files
        # e.g. if the workspace contains no packages
        '/opt/ros/%s' % rosdistro_name,
        '/tmp/ws/install_isolated',
    ]
    cmd += \
        ' --workspace-root /tmp/ws_overlay' + \
        ' --parent-result-space %s' % ' '.join(parent_result_spaces)
if vars().get('build_tool_args'):
    cmd += ' --build-tool-args ' + ' '.join(build_tool_args)
}@
CMD ["@cmd"]
