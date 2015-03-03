# generated from @template_name


@(TEMPLATE(
    'snippet/from_base_image.Dockerfile.em',
    os_name=os_name,
    os_code_name=os_code_name,
    arch=arch,
))@
MAINTAINER Dirk Thomas dthomas+buildfarm@@osrfoundation.org

VOLUME ["/var/cache/apt/archives"]

ENV DEBIAN_FRONTEND noninteractive
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8

@(TEMPLATE(
    'snippet/add_distribution_repositories.Dockerfile.em',
    distribution_repository_keys=distribution_repository_keys,
    distribution_repository_urls=distribution_repository_urls,
    os_code_name=os_code_name,
    add_source=False,
))@

@(TEMPLATE(
    'snippet/add_wrapper_scripts.Dockerfile.em',
    wrapper_scripts=wrapper_scripts,
))@

# automatic invalidation once every day
RUN echo "@today_str"

@# Ubuntu before Trusty explicitly needs python3
@[if os_name == 'ubuntu' and os_code_name[0] not in ['t', 'u']]@
RUN python -u /tmp/wrapper_scripts/apt-get.py update-and-install -q -y python3
@[end if]@

# always invalidate to actually have the latest apt repo state
RUN echo "@now_str"

RUN python3 -u /tmp/wrapper_scripts/apt-get.py update

ENTRYPOINT ["sh", "-c"]
CMD ["dpkg -i --force-depends /tmp/binarydeb/*.deb && apt-get -f -y install"]
