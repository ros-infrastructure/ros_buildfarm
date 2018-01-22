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

RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y ccache

@(TEMPLATE(
    'snippet/install_dependencies.Dockerfile.em',
    dependencies=dependencies,
    dependency_versions=dependency_versions,
))@

USER buildfarm
ENTRYPOINT ["sh", "-c"]
@{
cmd = \
    'PATH=/usr/lib/ccache:$PATH' + \
    ' PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u'
if not testing:
    cmd += \
        ' /tmp/ros_buildfarm/scripts/devel/catkin_make_isolated_and_install.py' + \
        ' --rosdistro-name %s --clean-before' % rosdistro_name
else:
    cmd += \
        ' /tmp/ros_buildfarm/scripts/devel/catkin_make_isolated_and_test.py' + \
        ' --rosdistro-name %s' % rosdistro_name
if not prerelease_overlay:
    cmd += \
        ' --workspace-root /tmp/catkin_workspace'
else:
    parent_result_spaces = [
        # also specify /opt/ros in case the install location has no setup files
        # e.g. if the workspace contains no packages
        '/opt/ros/%s' % rosdistro_name,
        '/tmp/catkin_workspace/install_isolated',
    ]
    cmd += \
        ' --workspace-root /tmp/catkin_workspace_overlay' + \
        ' --parent-result-space %s' % ' '.join(parent_result_spaces)
}@
CMD ["@cmd"]
