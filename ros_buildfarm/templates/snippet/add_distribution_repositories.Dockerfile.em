@[if package_format_mapping.get(os_name, 'deb') == 'deb']@
RUN mkdir -p /etc/apt/keyrings
@{
debian_before_stretch = ('squeeze', 'wheezy', 'jessie')
ubuntu_before_bionic = (
    'precise', 'quantal', 'raring', 'saucy',
    'trusty', 'utopic', 'vivid', 'wily',
    'xenial', 'yakkety', 'zesty', 'artful')
}@
@[if os_name == 'debian' and os_code_name not in debian_before_stretch or os_name == 'ubuntu' and os_code_name not in ubuntu_before_bionic]@
@# In Debian Stretch apt doesn't depend on gnupg anymore
@# https://anonscm.debian.org/cgit/apt/apt.git/commit/?id=87d468fe355c87325c943c40043a0bb236b2407f
RUN for i in 1 2 3; do apt-get update && apt-get install -q -y gnupg ca-certificates && apt-get clean && break || if [ $i -lt 3 ]; then sleep 5; else false; fi; done
@[end if]@
@[for i, key in enumerate(distribution_repository_keys)]@
RUN echo "@('\\n'.join(key.splitlines()))" > /etc/apt/keyrings/ros-buildfarm-@(i).asc
@[end for]@
@[for i, url in enumerate(distribution_repository_urls)]@
RUN echo deb [@[if distribution_repository_keys[i]]signed-by=/etc/apt/keyrings/ros-buildfarm-@(i).asc@[else]trusted=yes@[end if]] @url @os_code_name main | tee -a /etc/apt/sources.list.d/buildfarm.list
@[if add_source and url == target_repository]@
RUN echo deb-src [@[if distribution_repository_keys[i]]signed-by=/etc/apt/keyrings/ros-buildfarm-@(i).asc@[else]trusted=yes@[end if]] @url @os_code_name main | tee -a /etc/apt/sources.list.d/buildfarm.list
@[end if]@
@[end for]@
@# On Ubuntu Trusty a newer version of dpkg is required to install Debian packages created by stdeb on newer distros
@[if os_name == 'ubuntu' and os_code_name == 'trusty']@
RUN for i in 1 2 3; do apt-get update && apt-get install -q -y dpkg && apt-get clean && break || if [ $i -lt 3 ]; then sleep 5; else false; fi; done
@[end if]@
@[elif package_format_mapping.get(os_name) == 'rpm']@
RUN mkdir -p /etc/pki/rpm-gpg
@[for i, key in enumerate(distribution_repository_keys)]@
@[if key]@
RUN cat << 'EOF' > /etc/pki/rpm-gpg/ros-buildfarm-@(i).key
@key
EOF
@[else]@
RUN touch /etc/pki/rpm-gpg/ros-buildfarm-@(i).key
@[end if]@
@[end for]@
@[for i, url in enumerate(distribution_repository_urls)]@
RUN echo "[ros-buildfarm-@(i)]" > /etc/yum.repos.d/ros-buildfarm-@(i).repo && \
    echo "name=ROS Buildfarm Repository @(i)" >> /etc/yum.repos.d/ros-buildfarm-@(i).repo && \
    echo "baseurl=@url" >> /etc/yum.repos.d/ros-buildfarm-@(i).repo && \
    echo "enabled=1" >> /etc/yum.repos.d/ros-buildfarm-@(i).repo && \
    echo "gpgcheck=@(1 if len(distribution_repository_keys) > i and distribution_repository_keys[i] else 0)" >> /etc/yum.repos.d/ros-buildfarm-@(i).repo@[if len(distribution_repository_keys) > i and distribution_repository_keys[i]] && \
    echo "gpgkey=file:///etc/pki/rpm-gpg/ros-buildfarm-@(i).key" >> /etc/yum.repos.d/ros-buildfarm-@(i).repo@[end if]
@[end for]@
@[end if]@
