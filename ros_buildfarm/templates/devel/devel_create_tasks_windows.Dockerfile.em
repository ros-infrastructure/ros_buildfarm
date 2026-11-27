# escape=`
# generated from @template_name

@(TEMPLATE(
    'snippet/from_base_image.Dockerfile.em',
    base_image='mcr.microsoft.com/windows/server:%s' % os_code_name,
))@

# automatic invalidation once every day
RUN echo "@today_str"

@(TEMPLATE('snippet/install_pixi_windows.Dockerfile.em'))@

@# TODO: the Python version is per ROS distro (REP 2000), this is Rolling's
RUN pixi add python=3.14 git empy pyyaml
@# rosdep needs to be 0.27.0 or newer for the conda installer
RUN pixi add --pypi catkin_pkg rosdep rosdistro rospkg
RUN pixi --color never --no-progress -q list

# always invalidate to actually have the latest rosdep state
RUN echo "@now_str"

ENV ROSDISTRO_INDEX_URL=@rosdistro_index_url

@(TEMPLATE(
    'snippet/rosdep_init_pixi.Dockerfile.em',
    custom_rosdep_urls=custom_rosdep_urls,
))@

ENV PYTHONPATH=C:\ros_buildfarm
@{
cmds = [
    ' '.join(['pixi', 'run', 'rosdep', 'update'] + rosdep_update_options),
]
workspace_root = 'C:\\ws'
if prerelease_overlay:
    workspace_root += ' C:\\ws2'
cmd = \
    'pixi run python -u' + \
    ' C:\\ros_buildfarm\\scripts\\devel\\create_devel_task_generator.py' + \
    ' --rosdistro-name ' + rosdistro_name + \
    ' --workspace-root ' + workspace_root + \
    ' --os-name ' + os_name + \
    ' --os-code-name ' + os_code_name + \
    ' --arch ' + arch + \
    ' --distribution-repository-urls ' + ' '.join(distribution_repository_urls) + \
    ' --build-tool ' + build_tool + \
    ' --ros-version ' + str(ros_version) + \
    ' --env-vars ' + ' '.join(['%s=%s' % key_value for key_value in env_vars.items()])
if run_abichecker:
    cmd += ' --run-abichecker'
if require_gpu_support:
    cmd += ' --require-gpu-support'
cmds += [
    cmd +
    ' --dockerfile-dir C:\\docker_build_and_install' +
    ' --build-tool-args ' + ' '.join(build_tool_args or []),
    cmd +
    ' --dockerfile-dir C:\\docker_build_and_test' +
    ' --testing' +
    ' --build-tool-args ' + ' '.join(build_tool_args or []) +
    ' --build-tool-test-args ' + ' '.join(build_tool_test_args or []),
]
}@
# Shell form so that cmd.exe runs it
CMD "@(' && '.join(cmds))"
