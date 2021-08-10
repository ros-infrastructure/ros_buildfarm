@{
package_manager = 'dnf'
python3_pkgversion = '3'

if os_name == 'rhel' and os_code_name.isnumeric() and int(os_code_name) < 8:
    package_manager = 'yum'
    python3_pkgversion = '36'
}@
# generated from @template_name

@[if os_name in ['rhel']]@
FROM centos:@(os_code_name)

# Enable EPEL on RHEL
RUN @(package_manager) install -y epel-release
@[else]@
FROM @(os_name):@(os_code_name)
@[end if]@

RUN @(package_manager) update -y
RUN @(package_manager) install -y dnf{,-command\(download\)} mock{,-{core-configs,scm}} python@(python3_pkgversion){,-{catkin_pkg,empy,rosdistro,yaml}}

RUN useradd -u @(uid) -l -m buildfarm
RUN usermod -a -G mock buildfarm

# Clean up after updates and freshen cache
RUN @(package_manager) clean dbcache packages
RUN @(package_manager) makecache

# "Expire" the cache to force the next operation to check again
RUN @(package_manager) clean expire-cache

# automatic invalidation once every day
RUN echo "@(today_str)"

RUN @(package_manager) update -y

@[for i, key in enumerate(distribution_repository_keys)]@
RUN echo -e "@('\\n'.join(key.splitlines()))" > /etc/pki/mock/RPM-GPG-KEY-ros-buildfarm-@(i)
@[end for]@
COPY mock_config.cfg /etc/mock/ros_buildfarm.cfg

USER buildfarm
ENTRYPOINT ["sh", "-c"]
@{
cmds = [
    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' +
    ' /tmp/ros_buildfarm/scripts/release/rpm/get_sourcepkg.py' +
    ' --rosdistro-index-url ' + rosdistro_index_url +
    ' ' + rosdistro_name +
    ' ' + package_name +
    ' --sourcepkg-dir ' + sourcepkg_dir +
    (' --skip-download-sourcepkg' if skip_download_sourcepkg else ''),

    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' +
    ' /tmp/ros_buildfarm/scripts/release/rpm/build_binarypkg.py' +
    ' ' + rosdistro_name +
    ' ' + package_name +
    ' --sourcepkg-dir ' + sourcepkg_dir +
    ' --binarypkg-dir ' + binarypkg_dir +
    (' --append-timestamp' if append_timestamp else ''),
]
}@
CMD ["@(' && '.join(cmds))"]
