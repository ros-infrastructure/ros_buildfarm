# generated from @template_name
@{
global os
import os
}@

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
    'snippet/rosdep_init.Dockerfile.em',
    custom_rosdep_urls=custom_rosdep_urls,
))@

USER buildfarm
ENTRYPOINT ["sh", "-c"]
@{
install_paths = [os.path.join(root, 'install_isolated') for root in workspace_root[0:-1]]
base_paths = [path for root in install_paths for path in (os.path.join(root, '*', 'share'), os.path.join(root, 'share'))] + [workspace_root[-1]]
cmds = [
    'rosdep update',

    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' + \
    ' /tmp/ros_buildfarm/scripts/ci/create_workspace.py' + \
    ' --workspace-root ' + workspace_root[-1] + \
    ' --repos-file-urls ' + ' '.join(repos_file_urls) + \
    ' --test-branch "%s"' % (test_branch),

    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' + \
    ' /tmp/ros_buildfarm/scripts/ci/generate_install_lists.py' + \
    ' ' + rosdistro_name + \
    ' ' + os_name + \
    ' ' + os_code_name + \
    ' --package-root ' + ' '.join(base_paths) + \
    ' --output-dir ' + workspace_root[-1] + \
    ' --skip-rosdep-keys ' + ' '.join(skip_rosdep_keys) + \
    ' --package-selection-args ' + ' '.join(package_selection_args),
]
cmd = ' && '.join(cmds).replace('\\', '\\\\').replace('"', '\\"')
}@
CMD ["@cmd"]
