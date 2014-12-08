# generated from @template_name

FROM @os_name:@os_code_name
MAINTAINER @maintainer_name @maintainer_email

VOLUME ["/var/cache/apt/archives"]

ENV DEBIAN_FRONTEND noninteractive
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8

RUN useradd -u @uid -m buildfarm

RUN mkdir /tmp/keys
@[for i, key in enumerate(distribution_repository_keys)]@
RUN echo "@('\\n'.join(key.splitlines()))" > /tmp/keys/@(i).key
RUN apt-key add /tmp/keys/@(i).key
@[end for]@
@[for url in distribution_repository_urls]@
RUN echo deb @url @os_code_name main | tee -a /etc/apt/sources.list.d/buildfarm.list
@[end for]@

# optionally manual cache invalidation for core Python packages
RUN echo "2014-11-20"

# automatic invalidation once every day
@{
import datetime
today_isoformat = datetime.date.today().isoformat()
}@
RUN echo "@today_isoformat"

RUN mkdir /tmp/wrapper_scripts
@[for filename in sorted(wrapper_scripts.keys())]@
RUN echo "@('\\n'.join(wrapper_scripts[filename].replace('"', '\\"').splitlines()))" > /tmp/wrapper_scripts/@(filename)
@[end for]@

RUN python3 -u /tmp/wrapper_scripts/apt-get.py update && python3 -u /tmp/wrapper_scripts/apt-get.py install -q -y git python3-apt python3-catkin-pkg python3-empy python3-rosdep python3-rosdistro

# TODO improve rosdep init/update performance, enable on-change invalidation
@{
import datetime
now_isoformat = datetime.datetime.today().isoformat()
}@
RUN echo "@now_isoformat"
ENV ROSDISTRO_INDEX_URL @rosdistro_index_url
RUN rosdep init

USER buildfarm

ENTRYPOINT ["sh", "-c"]
@{
cmds = [
'rosdep update',
]
cmd = \
    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' + \
    ' /tmp/ros_buildfarm/scripts/devel/create_devel_task_generator.py' + \
    ' --rosdistro-name ' + rosdistro_name + \
    ' --workspace-root /tmp/catkin_workspace' + \
    ' --os-name ' + os_name + \
    ' --os-code-name ' + os_code_name + \
    ' --distribution-repository-urls ' + ' '.join(distribution_repository_urls) + \
    ' --distribution-repository-key-files ' + ' ' .join(['/tmp/keys/%d.key' % i for i in range(len(distribution_repository_keys))])
cmds += [
    cmd +
    ' --dockerfile-dir /tmp/docker_build_and_install',
    cmd +
    ' --dockerfile-dir /tmp/docker_build_and_test' +
    ' --testing',
]
}@
CMD ["@(' && '.join(cmds))"]
