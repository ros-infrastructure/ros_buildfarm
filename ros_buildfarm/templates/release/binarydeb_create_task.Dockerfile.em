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
    add_source=True,
    target_repository=target_repository,
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
    'snippet/install_apt-src.Dockerfile.em',
    os_name=os_name,
    os_code_name=os_code_name,
))@

RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y devscripts dpkg-dev python3-apt python3-catkin-pkg-modules python3-empy python3-rosdistro-modules python3-yaml

# always invalidate to actually have the latest apt repo state
RUN echo "@now_str"
RUN python3 -u /tmp/wrapper_scripts/apt.py update

USER buildfarm
ENTRYPOINT ["sh", "-c"]
@{
cmds = [
    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' +
    ' /tmp/ros_buildfarm/scripts/release/get_sourcedeb.py' +
    ' --rosdistro-index-url ' + rosdistro_index_url +
    ' ' + rosdistro_name +
    ' ' + package_name +
    ' --sourcedeb-dir ' + binarydeb_dir +
    (' --skip-download-sourcedeb' if skip_download_sourcedeb else ''),
]

if append_timestamp:
    cmds.append(
        'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' +
        ' /tmp/ros_buildfarm/scripts/release/append_build_timestamp.py' +
        ' ' + rosdistro_name +
        ' ' + package_name +
        ' --sourcedeb-dir ' + binarydeb_dir)

cmds.append(
    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' +
    ' /tmp/ros_buildfarm/scripts/release/create_binarydeb_task_generator.py' +
    ' --rosdistro-index-url ' + rosdistro_index_url +
    ' ' + rosdistro_name +
    ' ' + package_name +
    ' ' + os_name +
    ' ' + os_code_name +
    ' ' + arch +
    ' --distribution-repository-urls ' + ' '.join(distribution_repository_urls) +
    ' --distribution-repository-key-files ' + ' ' .join(['/tmp/keys/%d.key' % i for i in range(len(distribution_repository_keys))]) +
    ' --binarydeb-dir ' + binarydeb_dir +
    ' --dockerfile-dir ' + dockerfile_dir)
}@
CMD ["@(' && '.join(cmds))"]
