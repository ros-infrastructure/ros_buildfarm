@# Ubuntu raring and older are checked for official docker images generation
@# https://github.com/osrf/docker_images/pull/273
@[if os_name == 'ubuntu' and os_code_name in ['lucid', 'maverick', 'natty', 'oneiric', 'precise', 'quantal', 'raring', 'saucy', 'utopic', 'vivid', 'wily', 'yakkety', 'zesty', 'artful']]@
RUN find /etc/apt/ -name *.list -exec sed -i -e 's/archive.ubuntu.com\|security.ubuntu.com/old-releases.ubuntu.com/g' {} \;
@[end if]@
