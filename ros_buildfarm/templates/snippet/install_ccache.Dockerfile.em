@[if os_name == 'ubuntu' and os_code_name in ['trusty', 'utopic', 'vivid'] or os_name == 'debian' and os_code_name in ['jessie']]@
@# We need ccache 3.2 or higher: https://github.com/ros-infrastructure/buildfarm_deployment/issues/113
RUN python3 -u /tmp/wrapper_scripts/apt-get.py update-and-install -q -y curl gcc make
RUN curl https://www.samba.org/ftp/ccache/ccache-3.2.4.tar.bz2 -o /tmp/ccache.tar.gz
RUN tar -xf /tmp/ccache.tar.gz --directory /tmp
RUN mkdir -p /usr/lib/ccache
RUN cd /tmp/ccache-3.2.4 && ./configure && make && make install
RUN ln -s /usr/local/bin/ccache /usr/lib/ccache/gcc
RUN ln -s /usr/local/bin/ccache /usr/lib/ccache/cc
@[else]@
RUN python3 -u /tmp/wrapper_scripts/apt-get.py update-and-install -q -y ccache
@[end if]@
