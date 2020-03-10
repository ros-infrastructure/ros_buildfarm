include('/etc/mock/default.cfg')

# Change the root name since we're modifying the chroot
config_opts['root'] += '-ros-buildfarm'

# Add python3-rpm-macros to resolve %{python3_pkgversion} in rosdep rules
config_opts['chroot_setup_cmd'] += ' python3-rpm-macros'

# Install weak dependencies to get group members
config_opts['yum_builddep_opts'] = config_opts.get('yum_builddep_opts', []) + ['--setopt=install_weak_deps=True']
config_opts['dnf_builddep_opts'] = config_opts.get('dnf_builddep_opts', []) + ['--setopt=install_weak_deps=True']
config_opts['microdnf_builddep_opts'] = config_opts.get('microdnf_builddep_opts', []) + ['--setopt=install_weak_deps=True']

@[if build_environment_variables]@
# Set environment vars from the build config
@[for env_key, env_val in env_vars]@
config_opts['environment']['@env_key'] = '@env_val'
@[end for]
@[end if]@
# Disable debug packages until infrastructure can handle it
config_opts['macros']['debug_package'] = '%{nil}'

# Hack the %{dist} macro to allow release suffixing
config_opts['macros']['%dist'] = '.' + config_opts['dist'] + '%{?dist_suffix}'

# Required for running mock in Docker
config_opts['use_nspawn'] = False

@[if os_name in ['centos', 'rhel'] and os_code_name == '7']@
# Inject g++ 8 into RHEL 7 builds
config_opts['chroot_setup_cmd'] += ' devtoolset-8-gcc-c++ devtoolset-8-make-nonblocking'
config_opts['macros']['_buildshell'] = '/usr/bin/scl enable devtoolset-8 -- /bin/sh'

# Disable weak dependencies on RHEL 7 builds
config_opts['macros']['_without_weak_deps'] = '1'
@[else]@
# Add g++, which is an assumed dependency in ROS
config_opts['chroot_setup_cmd'] += ' gcc-c++ make'
@[end if]@

config_opts['yum.conf'] += """
@[for i, url in enumerate(distribution_repository_urls)]@
[ros-buildfarm-@(i)]
name=ROS Buildfarm Repository @(i) - $basearch
baseurl=@(url)
gpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-ros-buildfarm-@(i)
gpgcheck=@(1 if i < len(distribution_repository_keys) and distribution_repository_keys[i] else 0)
enabled=1

@[end for]@
@[if target_repository]@
[ros-buildfarm-target-source]
name=ROS Buildfarm Repository Target - SRPMS
baseurl=@(target_repository)
gpgcheck=0
enabled=0

@[end if]@
"""
