@[if os_name == 'ubuntu' and os_code_name in ['trusty', 'utopic', 'vivid'] or os_name == 'debian' and os_code_name in ['jessie']]@
@# We need ccache 3.2 or higher: https://github.com/ros-infrastructure/buildfarm_deployment/issues/113
RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y curl gcc make
RUN curl https://www.samba.org/ftp/ccache/ccache-3.2.4.tar.gz -o /tmp/ccache.tar.gz && tar -xf /tmp/ccache.tar.gz --directory /tmp
RUN mkdir -p /usr/lib/ccache
RUN cd /tmp/ccache-3.2.4 && ./configure && make && make install
RUN ln -s /usr/local/bin/ccache /usr/lib/ccache/c++
RUN ln -s /usr/local/bin/ccache /usr/lib/ccache/cc
RUN ln -s /usr/local/bin/ccache /usr/lib/ccache/g++
RUN ln -s /usr/local/bin/ccache /usr/lib/ccache/gcc
@[else]@
RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y ccache
@[end if]@
