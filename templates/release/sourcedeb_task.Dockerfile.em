FROM @os_name:@os_code_name
MAINTAINER @maintainer_name @maintainer_email

VOLUME ["/var/cache/apt/archives"]

ENV DEBIAN_FRONTEND noninteractive

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

# automatic invalidation once every day
@{
import datetime
today_isoformat = datetime.date.today().isoformat()
}@
RUN echo "@today_isoformat"

RUN apt-get update

# get_sources dependencies
# TODO use python3-rosdistro instead of source checkout
RUN apt-get install -q -y git python3 python3-catkin-pkg python3-yaml
# build_sourcedeb dependencies
RUN apt-get install -q -y debhelper dpkg dpkg-dev git-buildpackage
# upload_sourcedeb dependencies
RUN apt-get install -q -y openssh-client

USER buildfarm
ENTRYPOINT ["sh", "-c"]
@{
cmds = [
    'PYTHONPATH=/tmp/ros_buildfarm:/tmp/rosdistro/src:$PYTHONPATH python3 -u' +
    ' /tmp/ros_buildfarm/scripts/release/get_sources.py' +
    ' --rosdistro-index-url ' + rosdistro_index_url +
    ' ' + rosdistro_name +
    ' ' + package_name +
    ' ' + os_name +
    ' ' + os_code_name +
    ' --source-dir /tmp/sourcedeb/source',

    'PYTHONPATH=/tmp/ros_buildfarm:/tmp/rosdistro/src:$PYTHONPATH python3 -u' +
    ' /tmp/ros_buildfarm/scripts/release/build_sourcedeb.py' +
    ' --source-dir /tmp/sourcedeb/source',

#    'PYTHONPATH=/tmp/ros_buildfarm:$PYTHONPATH python3 -u ' +
#    '/tmp/ros_buildfarm/scripts/release/upload_sourcedeb.py',
]
}@
CMD ["@(' && '.join(cmds))"]
