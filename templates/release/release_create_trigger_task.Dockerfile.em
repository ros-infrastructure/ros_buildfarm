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

# optionally manual cache invalidation for core Python packages
RUN echo "2014-10-20"

# automatic invalidation once every day
@{
import datetime
today_isoformat = datetime.date.today().isoformat()
}@
RUN echo "@today_isoformat"

RUN mkdir /tmp/wrapper_scripts
@[for filename, content in wrapper_scripts.items()]@
RUN echo "@('\\n'.join(content.replace('"', '\\"').splitlines()))" > /tmp/wrapper_scripts/@(filename)
@[end for]@

RUN python3 -u /tmp/wrapper_scripts/apt-get.py update
RUN python3 -u /tmp/wrapper_scripts/apt-get.py install -q -y python3-empy python3-pip python3-yaml
RUN pip3 install jenkinsapi

USER buildfarm
ENTRYPOINT ["sh", "-c"]
@{
cmd = \
    'PYTHONPATH=/tmp/ros_buildfarm:/tmp/rosdistro/src:$PYTHONPATH python3 -u' + \
    ' /tmp/ros_buildfarm/scripts/release/trigger_jobs.py' + \
    ' --rosdistro-index-url ' + rosdistro_index_url + \
    ' ' + rosdistro_name + \
    ' ' + release_build_name + \
    ' --cache-dir ' + cache_dir
if missing_only:
    cmd += ' --missing-only'
if source_only:
    cmd += ' --source-only'
}@
CMD ["@cmd"]
