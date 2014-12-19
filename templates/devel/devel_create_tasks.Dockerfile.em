# generated from @template_name

FROM @os_name:@os_code_name
MAINTAINER @maintainer_name @maintainer_email

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
    add_source=False,
))@

# optionally manual cache invalidation for core Python packages
RUN echo "2014-11-20"

# automatic invalidation once every day
RUN echo "@today_str"

RUN mkdir /tmp/wrapper_scripts
@[for filename in sorted(wrapper_scripts.keys())]@
RUN echo "@('\\n'.join(wrapper_scripts[filename].replace('"', '\\"').splitlines()))" > /tmp/wrapper_scripts/@(filename)
@[end for]@

RUN python3 -u /tmp/wrapper_scripts/apt-get.py update && python3 -u /tmp/wrapper_scripts/apt-get.py install -q -y git python3-apt python3-catkin-pkg python3-empy python3-rosdep python3-rosdistro

# always invalidate to actually have the latest rosdep state
RUN echo "@now_str"
ENV ROSDISTRO_INDEX_URL @rosdistro_index_url
RUN rosdep init

USER buildfarm

ENTRYPOINT ["sh", "-c"]
@{
cmds = [
'rosdep update',
]
workspace_root = '/tmp/catkin_workspace'
if prerelease_overlay:
    workspace_root += ' /tmp/catkin_workspace_overlay'
cmd = \
    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' + \
    ' /tmp/ros_buildfarm/scripts/devel/create_devel_task_generator.py' + \
    ' --rosdistro-name ' + rosdistro_name + \
    ' --workspace-root ' + workspace_root + \
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
