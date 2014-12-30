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

@(TEMPLATE(
    'snippet/add_wrapper_scripts.Dockerfile.em',
    wrapper_scripts=wrapper_scripts,
))@

RUN python3 -u /tmp/wrapper_scripts/apt-get.py update-and-install -q -y git python3-catkin-pkg python3-rosdistro python3-yaml

USER buildfarm
ENTRYPOINT ["sh", "-c"]
@{
cmds = [
    'cd /tmp/rosdistro_cache',
    'python3 -u' +
    ' /usr/bin/rosdistro_build_cache' +
    ' ' + rosdistro_index_url +
    ' ' + rosdistro_name +
    ' --debug --ignore-local'
]
}@
CMD ["@(' && '.join(cmds))"]
