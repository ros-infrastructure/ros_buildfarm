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

# optionally manual cache invalidation for core Python packages
RUN echo "2014-11-20"

# automatic invalidation once every day
RUN echo "@today_str"

@(TEMPLATE(
    'snippet/add_wrapper_scripts.Dockerfile.em',
    wrapper_scripts=wrapper_scripts,
))@

RUN python3 -u /tmp/wrapper_scripts/apt-get.py update-and-install -q -y python3-empy python3-pip python3-rosdistro python3-yaml
RUN pip3 install jenkinsapi

USER buildfarm
ENTRYPOINT ["sh", "-c"]
@{
cmd = \
    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' + \
    ' /tmp/ros_buildfarm/scripts/release/trigger_jobs.py' + \
    ' ' + config_url + \
    ' ' + rosdistro_name + \
    ' ' + release_build_name + \
    ' --cause "%s"' % cause + \
    ' --cache-dir ' + cache_dir
if missing_only:
    cmd += ' --missing-only'
if source_only:
    cmd += ' --source-only'
}@
CMD ["@(cmd.replace('"', '\\"'))"]
