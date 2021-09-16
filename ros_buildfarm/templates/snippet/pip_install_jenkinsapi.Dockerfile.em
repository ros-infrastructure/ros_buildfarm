@[if os_code_name == 'xenial']@
RUN python3 -u /tmp/wrapper_scripts/apt.py update-install-clean -q -y git
RUN pip3 install jenkinsapi git+https://github.com/Ousret/charset_normalizer.git@@0c52bfecd4b8f033b2599496551d86b370a08bc8
@[else]@
RUN pip3 install jenkinsapi
@[end if]@
