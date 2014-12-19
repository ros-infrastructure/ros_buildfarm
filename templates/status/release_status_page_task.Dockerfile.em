# generated from @template_name

FROM @os_name:@os_code_name
MAINTAINER @maintainer_name @maintainer_email

VOLUME ["/var/cache/apt/archives"]

ENV DEBIAN_FRONTEND noninteractive
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8

RUN useradd -u @uid -m buildfarm

@(TEMPLATE(
    'snippet/add_distribution_repositories.Dockerfile.em',
    distribution_repository_keys=distribution_repository_keys,
    distribution_repository_urls=distribution_repository_urls,
    os_code_name=os_code_name,
    add_source=False,
))@

# optionally manual cache invalidation for core dependencies
RUN echo "2014-11-20"

# automatic invalidation once every day
RUN echo "@today_str"

RUN mkdir /tmp/wrapper_scripts
@[for filename in sorted(wrapper_scripts.keys())]@
RUN echo "@('\\n'.join(wrapper_scripts[filename].replace('"', '\\"').splitlines()))" > /tmp/wrapper_scripts/@(filename)
@[end for]@

RUN python3 -u /tmp/wrapper_scripts/apt-get.py update && python3 -u /tmp/wrapper_scripts/apt-get.py install -q -y git python3-catkin-pkg python3-empy python3-rosdistro python3-yaml

USER buildfarm
ENTRYPOINT ["sh", "-c"]
@{
cmd = \
    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' + \
    ' /tmp/ros_buildfarm/scripts/status/build_release_status_page.py' + \
    ' ' + config_url + \
    ' ' + rosdistro_name + \
    ' ' + release_build_name + \
    ' --output-dir /tmp/status_page' + \
    ' --copy-resources'
}@
CMD ["@cmd"]
