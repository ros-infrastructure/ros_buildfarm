FROM @os_name:@os_code_name
MAINTAINER @maintainer_name @maintainer_email

VOLUME ["/var/cache/apt/archives"]

ENV DEBIAN_FRONTEND noninteractive
RUN locale-gen en_US.UTF-8
ENV LANG en_US.UTF-8

RUN useradd -u @uid -m buildfarm

RUN mkdir /tmp/keys
@[for i, key in enumerate(distribution_repository_keys)]@
RUN echo "@('\\n'.join(key.splitlines()))" > /tmp/keys/@(i).key
RUN apt-key add /tmp/keys/@(i).key
@[end for]@
@[for url in distribution_repository_urls]@
RUN echo deb @url @os_code_name main | tee -a /etc/apt/sources.list.d/buildfarm.list
@[end for]@

# optionally manual cache invalidation for core dependencies
RUN echo "2014-10-20"

# if any dependency version has changed invalidate cache
@[for k in sorted(dependency_versions.keys())]@
RUN echo "@k: @dependency_versions[k]"
@[end for]@

# automatic invalidation once every day
@{
import datetime
today_isoformat = datetime.date.today().isoformat()
}@
RUN echo "@today_isoformat"

ADD apt-get.py /tmp/
RUN python3 -u /tmp/apt-get.py update

@[for d in dependencies]@
RUN python3 -u /tmp/apt-get.py install -q -y @d
@[end for]@

USER buildfarm
ENTRYPOINT ["sh", "-c"]
@{
cmd = \
    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u' + \
    ' /tmp/ros_buildfarm/scripts/release/build_binarydeb.py' + \
    ' ' + rosdistro_name + \
    ' ' + package_name + \
    ' --sourcedeb-dir ' + binarydeb_dir
}@
CMD ["@cmd"]
