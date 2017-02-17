# generated from @template_name

FROM ubuntu:trusty

VOLUME ["/var/cache/apt/archives"]

ENV DEBIAN_FRONTEND noninteractive

@(TEMPLATE(
    'snippet/setup_locale.Dockerfile.em',
    os_name='ubuntu',
    os_code_name='trusty',
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

RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y make python-catkin-pkg-modules python-dateutil python-pip python-wstool python-yaml
RUN pip install -U catkin-sphinx sphinx

USER buildfarm

ENTRYPOINT ["sh", "-c"]
@{
cmd = '/tmp/ros_buildfarm/scripts/doc/invoke_doc_targets.sh' + \
    ' /tmp/repositories' + \
    ' /tmp/generated_documentation/independent/api'
}@
CMD ["@cmd"]
