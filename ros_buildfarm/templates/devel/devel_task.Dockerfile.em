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

RUN useradd -u @uid -l -m buildfarm

@(TEMPLATE(
    'snippet/setup_nvidia_docker2.Dockerfile.em'
))@

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

@[if run_abichecker]@
RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y python3 abi-compliance-checker python3-catkin-pkg-modules
RUN pip3 install -U auto_abi_checker
@[end if]@

# After all dependencies are installed, update ccache symlinks.
# This command is supposed to be invoked whenever a new compiler is installed
# but that isn't happening. So we invoke it here to make sure all compilers are
# picked up.
# TODO(nuclearsandwich) add link to Debian bug report when one is opened.
RUN which update-ccache-symlinks >/dev/null 2>&1 && update-ccache-symlinks

USER buildfarm
ENTRYPOINT ["sh", "-c"]
@{
cmd = \
    'PATH=/usr/lib/ccache:$PATH' + \
    ' PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u'
if not testing:
    cmd += \
        ' /tmp/ros_buildfarm/scripts/devel/build_and_install.py' + \
        ' --rosdistro-name ' + rosdistro_name + \
        ' --ros-version ' + str(ros_version) + \
        ' --clean-before'
    if run_abichecker:
        cmd += ' --run-abichecker'
else:
    cmd += \
        ' /tmp/ros_buildfarm/scripts/devel/build_and_test.py' + \
        ' --rosdistro-name %s' % rosdistro_name
    if require_gpu_support:
        cmd += ' --require-gpu-support'
        if run_only_gpu_tests:
            cmd += ' --run-only-gpu-tests'
cmd += \
    ' --build-tool ' + build_tool + \
    ' --workspace-root ' + workspace_root + \
    ' --parent-result-space' + ''.join([' %s/install_isolated' % (space) for space in parent_result_space])
if vars().get('build_tool_args'):
    cmd += ' --build-tool-args ' + ' '.join(build_tool_args)
}@
CMD ["@cmd"]
