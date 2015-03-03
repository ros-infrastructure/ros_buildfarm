# generated from @template_name

@(TEMPLATE(
    'snippet/from_base_image.Dockerfile.em',
    os_name=os_name,
    os_code_name=os_code_name,
    arch=arch,
))@
MAINTAINER Dirk Thomas dthomas+buildfarm@@osrfoundation.org

VOLUME ["/var/cache/apt/archives"]

ENV DEBIAN_FRONTEND noninteractive
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV TZ @timezone

RUN useradd -u @uid -m buildfarm

@(TEMPLATE(
    'snippet/add_distribution_repositories.Dockerfile.em',
    distribution_repository_keys=distribution_repository_keys,
    distribution_repository_urls=distribution_repository_urls,
    os_code_name=os_code_name,
    add_source=True,
))@

@(TEMPLATE(
    'snippet/add_wrapper_scripts.Dockerfile.em',
    wrapper_scripts=wrapper_scripts,
))@

# automatic invalidation once every day
RUN echo "@today_str"

@# Ubuntu before Trusty explicitly needs python3
@[if os_name == 'ubuntu' and os_code_name[0] not in ['t', 'u']]@
RUN python -u /tmp/wrapper_scripts/apt-get.py update-and-install -q -y python3
@[end if]@

RUN python3 -u /tmp/wrapper_scripts/apt-get.py update-and-install -q -y devscripts dpkg-dev python3-apt python3-catkin-pkg python3-empy python3-rosdistro python3-yaml

# always invalidate to actually have the latest apt repo state
RUN echo "@now_str"
RUN python3 -u /tmp/wrapper_scripts/apt-get.py update

USER buildfarm
ENTRYPOINT ["sh", "-c"]
@{
cmds = [
    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' +
    ' /tmp/ros_buildfarm/scripts/release/get_sourcedeb.py' +
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
