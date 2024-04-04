include('/etc/mock/default.cfg')

# Change the root name since we're modifying the chroot
config_opts['root'] += '-ros-buildfarm'

# Disable mock bootstrapping
config_opts['use_bootstrap'] = False

# Add python3-rpm-macros to resolve %{python3_pkgversion} in rosdep rules
config_opts['chroot_setup_cmd'] += ' python3-rpm-macros'

# Install weak dependencies to get group members
config_opts[f'dnf_builddep_opts'] = config_opts.get(f'dnf_builddep_opts', []) + ['--setopt=install_weak_deps=True']

@[if env_vars]@
# Set environment vars from the build config
@[for env_key, env_val in env_vars.items()]@
config_opts['environment']['@env_key'] = '@env_val'
@[end for]
@[end if]@
# Make debuginfo/debugsource packages best-effort
config_opts['macros']['%_empty_manifest_terminate_build'] = '%{nil}'
config_opts['macros']['%_missing_build_ids_terminate_build'] = '%{nil}'

@[if os_name in ['rhel'] and os_code_name in ['8', '9']]@
# Disable automatic out-of-source CMake builds
config_opts['macros']['%__cmake_in_source_build'] = '1'
config_opts['macros']['%__cmake3_in_source_build'] = '1'
@[end if]@
# Required for running mock in Docker
config_opts['use_nspawn'] = False

# Add g++, which is an assumed dependency in ROS
config_opts['chroot_setup_cmd'] += ' gcc-c++ make'

config_opts[f'dnf.conf'] += """
@[for i, url in enumerate(distribution_repository_urls)]@
[ros-buildfarm-@(i)]
name=ROS Buildfarm Repository @(i) - $basearch
baseurl=@(url)
gpgkey=file:///etc/pki/mock/RPM-GPG-KEY-ros-buildfarm-@(i)
repo_gpgcheck=@(1 if i < len(distribution_repository_keys) and distribution_repository_keys[i] else 0)
gpgcheck=0
enabled=1
skip_if_unavailable=False

@[end for]@
@[if target_repository]@
[ros-buildfarm-target-source]
name=ROS Buildfarm Repository Target - SRPMS
baseurl=@(target_repository)
repo_gpgcheck=0
gpgcheck=0
enabled=0
skip_if_unavailable=False

@[end if]@
"""
