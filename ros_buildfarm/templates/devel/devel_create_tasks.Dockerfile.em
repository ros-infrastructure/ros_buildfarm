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
    'snippet/setup_locale.Dockerfile.em',
    timezone=timezone,
))@

RUN useradd -u @uid -l -m buildfarm

@[if require_gpu_support]@
@(TEMPLATE(
    'snippet/setup_nvidia_docker2.Dockerfile.em'
))@
@[end if]@

@(TEMPLATE(
    'snippet/add_distribution_repositories.Dockerfile.em',
    distribution_repository_keys=distribution_repository_keys,
    distribution_repository_urls=distribution_repository_urls,
    os_name=os_name,
    os_code_name=os_code_name,
    add_source=False,
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

RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y git python3-apt python3-catkin-pkg-modules python3-empy python3-rosdep python3-rosdistro-modules wget

# always invalidate to actually have the latest apt and rosdep state
RUN echo "@now_str"
RUN python3 -u /tmp/wrapper_scripts/apt.py update

ENV ROSDISTRO_INDEX_URL @rosdistro_index_url

@(TEMPLATE(
    'snippet/rosdep_init.Dockerfile.em',
    custom_rosdep_urls=custom_rosdep_urls,
))@

USER buildfarm

ENTRYPOINT ["sh", "-c"]
@{
cmds = [
    ' '.join(['rosdep', 'update'] + rosdep_update_options),
]
workspace_root = '/tmp/ws'
if prerelease_overlay:
    workspace_root += ' /tmp/ws2'
cmd = \
    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' + \
    ' /tmp/ros_buildfarm/scripts/devel/create_devel_task_generator.py' + \
    ' --rosdistro-name ' + rosdistro_name + \
    ' --workspace-root ' + workspace_root + \
    ' --os-name ' + os_name + \
    ' --os-code-name ' + os_code_name + \
    ' --arch ' + arch + \
    ' --distribution-repository-urls ' + ' '.join(distribution_repository_urls) + \
    ' --distribution-repository-key-files ' + ' ' .join(['/tmp/keys/%d.key' % i for i in range(len(distribution_repository_keys))]) + \
    ' --build-tool ' + build_tool + \
    ' --ros-version ' + str(ros_version) + \
    ' --env-vars ' + ' ' .join(['%s=%s' % key_value for key_value in env_vars.items()])
if run_abichecker:
    cmd += ' --run-abichecker'
if require_gpu_support:
    cmd += ' --require-gpu-support'
cmds += [
    cmd +
    ' --dockerfile-dir /tmp/docker_build_and_install' +
    ' --build-tool-args ' + ' '.join(build_tool_args or []),
    cmd +
    ' --dockerfile-dir /tmp/docker_build_and_test' +
    ' --testing' +
    ' --build-tool-args ' + ' '.join(build_tool_args or []) +
    ' --build-tool-test-args ' + ' '.join(build_tool_test_args or []),
]
}@
CMD ["@(' && '.join(cmds))"]
