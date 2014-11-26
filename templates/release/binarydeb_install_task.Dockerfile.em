# generated from @template_name

FROM @os_name:@os_code_name
MAINTAINER @maintainer_name @maintainer_email

VOLUME ["/var/cache/apt/archives"]

ENV DEBIAN_FRONTEND noninteractive
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8

RUN mkdir /tmp/keys
@[for i, key in enumerate(distribution_repository_keys)]@
RUN echo "@('\\n'.join(key.splitlines()))" > /tmp/keys/@(i).key
RUN apt-key add /tmp/keys/@(i).key
@[end for]@
@[for url in distribution_repository_urls]@
RUN echo deb @url @os_code_name main | tee -a /etc/apt/sources.list.d/buildfarm.list
@[end for]@

# always invalidate
@{
import datetime
now_isoformat = datetime.datetime.now().isoformat()
}@
RUN echo "@now_isoformat"

RUN mkdir /tmp/wrapper_scripts
@[for filename, content in wrapper_scripts.items()]@
RUN echo "@('\\n'.join(content.replace('"', '\\"').splitlines()))" > /tmp/wrapper_scripts/@(filename)
@[end for]@

RUN python3 -u /tmp/wrapper_scripts/apt-get.py update

ENTRYPOINT ["sh", "-c"]
CMD ["dpkg -i --force-depends /tmp/binarydeb/*.deb && apt-get -f -y install"]
