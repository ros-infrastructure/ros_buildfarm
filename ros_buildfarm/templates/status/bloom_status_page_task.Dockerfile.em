# generated from @template_name

FROM ubuntu:xenial

VOLUME ["/var/cache/apt/archives"]

ENV DEBIAN_FRONTEND noninteractive

@(TEMPLATE(
    'snippet/setup_locale.Dockerfile.em',
    timezone=timezone,
))@

RUN useradd -u @uid -m buildfarm

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

RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y git python3-pip python3-yaml python3-empy
RUN pip3 install pygithub requests

USER buildfarm
ENTRYPOINT ["sh", "-c"]
@{
cmd = \
    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH ROSDISTRO_INDEX_URL=' + rosdistro_index_url + ' python3 -u' + \
    ' /tmp/ros_buildfarm/scripts/status/build_bloom_status_page.py' + \
    ' --output-dir /tmp/bloom_status'
}@
CMD ["@cmd"]
