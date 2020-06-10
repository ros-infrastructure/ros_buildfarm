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

RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y git python3-apt python3-empy python3-yaml

# always invalidate to actually have the latest apt and rosdep state
RUN echo "@now_str"
RUN python3 -u /tmp/wrapper_scripts/apt.py update

USER buildfarm

@[for repos_file in repos_file_names]@
COPY @repos_file /tmp/@repos_file
@[end for]@

ENTRYPOINT ["sh", "-c"]
@{
args = \
    ' ' + rosdistro_name + \
    ' ' + os_name + \
    ' ' + os_code_name + \
    ' ' + arch + \
    ' --workspace-root ' + ' '.join(workspace_mount_point) + \
    ' --distribution-repository-urls ' + ' '.join(distribution_repository_urls) + \
    ' --distribution-repository-key-files ' + ' ' .join(['/tmp/keys/%d.key' % i for i in range(len(distribution_repository_keys))]) + \
    ' --env-vars ' + ' ' .join(['%s=%s' % key_value for key_value in env_vars.items()])
build_args = args + \
    ' --build-tool ' + build_tool + \
    ' --ros-version ' + str(ros_version) + \
    ' --install-packages ' + ' '.join(install_packages) + \
    ' --build-tool-args ' + ' '.join(build_tool_args or [])
cmds = [
    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' + \
    ' /tmp/ros_buildfarm/scripts/ci/create_workspace_task_generator.py' + \
    args + \
    ' --dockerfile-dir /tmp/docker_create_workspace' + \
    ' --repos-file-urls ' + ' '.join('file:///tmp/%s' % repos_file for repos_file in repos_file_names) + \
    ' --repository-names ' + ' '.join(repository_names) + \
    ' --test-branch "%s"' % (test_branch) + \
    ' --skip-rosdep-keys ' + ' '.join(skip_rosdep_keys) + \
    ' --package-selection-args ' + ' '.join(package_selection_args),

    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' + \
    ' /tmp/ros_buildfarm/scripts/ci/build_task_generator.py' + \
    ' --dockerfile-dir /tmp/docker_build_and_install' + \
    build_args,

    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' + \
    ' /tmp/ros_buildfarm/scripts/ci/build_task_generator.py' + \
    ' --testing' + \
    ' --dockerfile-dir /tmp/docker_build_and_test' + \
    build_args + \
    ' --build-tool-test-args ' + ' '.join(build_tool_test_args or []),
]
cmd = ' && '.join(cmds).replace('\\', '\\\\').replace('"', '\\"')
}@
CMD ["@cmd"]
