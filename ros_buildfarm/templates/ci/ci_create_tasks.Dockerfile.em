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

RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y git python3-apt python3-empy

# always invalidate to actually have the latest apt and rosdep state
RUN echo "@now_str"
RUN python3 -u /tmp/wrapper_scripts/apt.py update

USER buildfarm

ENTRYPOINT ["sh", "-c"]
@{
workspace_root = '/tmp/workspace'
args = \
    ' --workspace-root ' + workspace_root + \
    ' --rosdistro-name ' + rosdistro_name + \
    ' --os-name ' + os_name + \
    ' --os-code-name ' + os_code_name + \
    ' --arch ' + arch + \
    ' --distribution-repository-urls ' + ' '.join(distribution_repository_urls) + \
    ' --distribution-repository-key-files ' + ' ' .join(['/tmp/keys/%d.key' % i for i in range(len(distribution_repository_keys))])
cmds = [
    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' + \
    ' /tmp/ros_buildfarm/scripts/ci/create_workspace_task_generator.py' + \
    args + \
    ' --dockerfile-dir /tmp/docker_create_workspace' + \
    ' --repos-file-urls ' + ' '.join(repos_file_urls) + \
    ' --skip-rosdep-keys ' + ' '.join(skip_rosdep_keys),

    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' + \
    ' /tmp/ros_buildfarm/scripts/ci/colcon_build_task_generator.py' + \
    args + \
    ' --dockerfile-dir /tmp/docker_colcon_build',
]
}@
CMD ["@(' && '.join(cmds))"]
