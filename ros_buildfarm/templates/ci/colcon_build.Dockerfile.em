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

@(TEMPLATE(
    'snippet/install_ccache.Dockerfile.em',
    os_name=os_name,
    os_code_name=os_code_name,
))@

@(TEMPLATE(
    'snippet/install_dependencies.Dockerfile.em',
    dependencies=dependencies,
    dependency_versions=dependency_versions,
))@

ENV RTI_NC_LICENSE_ACCEPTED yes
COPY install_list.txt .
RUN xargs -a install_list.txt apt-get install -q -y

RUN update-ccache-symlinks
ENV PATH="/usr/lib/ccache:${PATH}"

USER buildfarm
ENTRYPOINT ["sh", "-c"]
@{
cmd = \
    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' + \
    ' /tmp/ros_buildfarm/scripts/ci/colcon_build.py' + \
    ' --workspace-root /tmp/colcon_workspace' + \
    ' --rosdistro-name ' + rosdistro_name + \
    ' --testing' + \
    ' --parent-result-space ' + ' '.join(parent_result_space)
}@
CMD ["@(cmd)"]
