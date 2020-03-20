# generated from @template_name

FROM ubuntu:xenial

VOLUME ["/var/cache/apt/archives"]

ENV DEBIAN_FRONTEND noninteractive

@(TEMPLATE(
    'snippet/setup_locale.Dockerfile.em',
    timezone=timezone,
))@

RUN useradd -u @uid -l -m buildfarm

@(TEMPLATE(
    'snippet/add_distribution_repositories.Dockerfile.em',
    distribution_repository_keys=distribution_repository_keys,
    distribution_repository_urls=distribution_repository_urls,
    os_name='ubuntu',
    os_code_name='xenial',
    add_source=False,
))@

@(TEMPLATE(
    'snippet/add_wrapper_scripts.Dockerfile.em',
    wrapper_scripts=wrapper_scripts,
))@

# automatic invalidation once every day
RUN echo "@today_str"

@(TEMPLATE(
    'snippet/install_python3.Dockerfile.em',
    os_name='ubuntu',
    os_code_name='xenial',
))@

RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y make python3-pip
@[if install_apt_packages]@
RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y @(' '.join(install_apt_packages))
@[end if]@
@[if install_pip_packages]@
RUN pip3 install -U @(' '.join(install_pip_packages))
@[end if]@

USER buildfarm

ENTRYPOINT ["sh", "-c"]
@{
cmd = '/tmp/ros_buildfarm/scripts/doc/invoke_doc_targets.sh' + \
    ' /tmp/repositories' + \
    ' /tmp/generated_documentation/independent/api'
}@
CMD ["@cmd"]
