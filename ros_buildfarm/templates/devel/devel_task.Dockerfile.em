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

RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y git python3-yaml

@[if build_tool == 'colcon']@
RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y python3-pip
@# colcon-core.package_identification.python needs at least setuptools 30.3.0
@# pytest-rerunfailures enables usage of --retest-until-pass
RUN pip3 install -U setuptools pytest-rerunfailures
@[end if]@
@[if ros_version == 2]@
RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y ros-@(rosdistro_name)-ros-workspace
@[end if]@
RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y ccache

@[if run_abichecker]@
RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y python3-catkin-pkg-modules python3-pip
@[if os_name == 'ubuntu' and os_code_name not in ('xenial', 'bionic')]@
# Focal/Groovy abi-compliance-checker package has a bug that breaks python invocation
# See: https://github.com/lvc/abi-compliance-checker/pull/80#issuecomment-652521014
# Install 2.3 version from source, needs perl
RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y curl make perl
RUN curl -sL https://github.com/lvc/abi-compliance-checker/archive/2.3.tar.gz | tar xvz -C /tmp && \
    make install prefix=/usr -C /tmp/abi-compliance-checker-2.3 && \
    rm -fr /tmp/abi-compliance
@[else]@
RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y abi-compliance-checker
@[end if]@
RUN pip3 install -U auto_abi_checker
@[end if]@

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
        ' --rosdistro-name %s' % rosdistro_name + \
        ' --ros-version ' + str(ros_version)
    if require_gpu_support:
        cmd += ' --require-gpu-support'
cmd += \
    ' --build-tool ' + build_tool + \
    ' --workspace-root ' + workspace_root + \
    ' --parent-result-space' + ''.join([' %s/install_isolated' % (space) for space in parent_result_space])
if vars().get('build_tool_args'):
    cmd += ' --build-tool-args ' + ' '.join(build_tool_args)
if vars().get('build_tool_test_args'):
    cmd += ' --build-tool-test-args ' + ' '.join(
        a if ' ' not in a else '"%s"' % a for a in build_tool_test_args)
}@
CMD ["@(cmd.replace('"', '\\"'))"]
