# generated from @template_name

FROM @os_name:@os_code_name
MAINTAINER @maintainer_name @maintainer_email

VOLUME ["/var/cache/apt/archives"]

ENV DEBIAN_FRONTEND noninteractive
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8
ENV TZ @timezone

RUN useradd -u @uid -m buildfarm

RUN mkdir /tmp/keys
@[for i, key in enumerate(distribution_repository_keys)]@
RUN echo "@('\\n'.join(key.splitlines()))" > /tmp/keys/@(i).key
RUN apt-key add /tmp/keys/@(i).key
@[end for]@
@[for url in distribution_repository_urls]@
RUN echo deb @url @os_code_name main | tee -a /etc/apt/sources.list.d/buildfarm.list
RUN echo deb-src @url @os_code_name main | tee -a /etc/apt/sources.list.d/buildfarm.list
@[end for]@

# optionally manual cache invalidation for core Python packages
RUN echo "2014-11-20"

@# Ubuntu before Trusty explicitly needs python3
@[if os_name == 'ubuntu' and os_code_name[0] < 't']@
RUN apt-get update && apt-get install -q -y python3
@[end if]@

# automatic invalidation once every day
RUN echo "@today_str"

RUN mkdir /tmp/wrapper_scripts
@[for filename in sorted(wrapper_scripts.keys())]@
RUN echo "@('\\n'.join(wrapper_scripts[filename].replace('"', '\\"').splitlines()))" > /tmp/wrapper_scripts/@(filename)
@[end for]@

RUN python3 -u /tmp/wrapper_scripts/apt-get.py update && python3 -u /tmp/wrapper_scripts/apt-get.py install -q -y devscripts dpkg-dev python3-apt python3-catkin-pkg python3-empy python3-rosdistro python3-yaml

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
