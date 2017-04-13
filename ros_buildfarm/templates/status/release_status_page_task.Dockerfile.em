# generated from @template_name

FROM ubuntu:trusty

VOLUME ["/var/cache/apt/archives"]

ENV DEBIAN_FRONTEND noninteractive

@(TEMPLATE(
    'snippet/setup_locale.Dockerfile.em',
    timezone=timezone,
))@

RUN useradd -u @uid -m buildfarm

@(TEMPLATE(
    'snippet/add_distribution_repositories.Dockerfile.em',
    distribution_repository_keys=distribution_repository_keys,
    distribution_repository_urls=distribution_repository_urls,
    os_name='ubuntu',
    os_code_name='trusty',
    add_source=False,
))@

@(TEMPLATE(
    'snippet/add_wrapper_scripts.Dockerfile.em',
    wrapper_scripts=wrapper_scripts,
))@

# automatic invalidation once every day
RUN echo "@today_str"

RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y git python3-catkin-pkg-modules python3-empy python3-rosdistro-modules python3-yaml

USER buildfarm
ENTRYPOINT ["sh", "-c"]
@{
cmd = \
    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' + \
    ' /tmp/ros_buildfarm/scripts/status/build_release_status_page.py' + \
    ' ' + config_url + \
    ' ' + rosdistro_name + \
    ' ' + release_build_name + \
    ' --cache-dir /tmp/debian_repo_cache' + \
    ' --output-dir /tmp/status_page' + \
    ' --copy-resources'
}@
CMD ["@cmd"]
