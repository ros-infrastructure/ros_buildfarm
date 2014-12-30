# generated from @template_name

FROM @os_name:@os_code_name
MAINTAINER @maintainer_name @maintainer_email

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

@# Ubuntu before Trusty explicitly needs python3
@[if os_name == 'ubuntu' and os_code_name[0] < 't']@
RUN apt-get update && apt-get install -q -y python3
@[end if]@

# always invalidate to actually have the latest apt repo state
RUN echo "@now_str"

@(TEMPLATE(
    'snippet/add_wrapper_scripts.Dockerfile.em',
    wrapper_scripts=wrapper_scripts,
))@

RUN python3 -u /tmp/wrapper_scripts/apt-get.py update

ENTRYPOINT ["sh", "-c"]
CMD ["dpkg -i --force-depends /tmp/binarydeb/*.deb && apt-get -f -y install"]
