# generated from @template_name

@[if os_name in ['rhel']]@
FROM almalinux:@(os_code_name)

# Enable CRB and EPEL on RHEL
RUN dnf install --refresh -y epel-release && crb enable
@[else]@
FROM @(os_name):@(os_code_name)
@[end if]@

RUN dnf update --refresh -y

RUN dnf install --refresh -y --setopt=install_weak_deps=False dnf{,-command\(download\)} git mock{,-{core-configs,scm}} python3{,-{catkin_pkg,empy,rosdistro,yaml}}

RUN useradd -u @(uid) -l -m buildfarm
RUN usermod -a -G mock buildfarm

# automatic invalidation once every day
RUN echo "@(today_str)"

RUN dnf update --refresh -y

# Workaround for broken mock configs for EPEL 8
RUN echo -e "include('templates/almalinux-8.tpl')\ninclude('templates/epel-8.tpl')\n\nconfig_opts['root'] = 'epel-8-x86_64'\nconfig_opts['target_arch'] = 'x86_64'\nconfig_opts['legal_host_arches'] = ('x86_64',)" > /etc/mock/epel-8-x86_64.cfg

@[for i, key in enumerate(distribution_repository_keys)]@
RUN echo -e "@('\\n'.join(key.splitlines()))" > /etc/pki/mock/RPM-GPG-KEY-ros-buildfarm-@(i)
@[end for]@
COPY mock_config.cfg /etc/mock/ros_buildfarm.cfg

USER buildfarm
ENTRYPOINT ["sh", "-c"]
@{
cmds = [
    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' +
    ' /tmp/ros_buildfarm/scripts/release/rpm/build_sourcepkg.py' +
    ' --rosdistro-index-url ' + rosdistro_index_url +
    ' ' + rosdistro_name +
    ' ' + package_name +
    ' ' + os_name +
    ' ' + os_code_name +
    ' --source-dir ' + sourcepkg_dir,
]
}@
CMD ["@(' && '.join(cmds))"]
