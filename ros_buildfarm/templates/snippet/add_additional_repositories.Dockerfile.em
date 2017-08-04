@[if os_name == 'ubuntu']@
@{
from itertools import product
}@
@[  if arch in ['amd64', 'i386']]@
@{
archive_commands = []
old_releases_commands = []
for distribution, archive_type in product((os_code_name, os_code_name + '-updates', os_code_name + '-security'), ('deb', 'deb-src')):
    archive_commands.append('echo "%s http://archive.ubuntu.com/ubuntu/ %s multiverse" >> /etc/apt/sources.list' % (archive_type, distribution))
    old_releases_commands.append('echo "%s http://old-releases.ubuntu.com/ubuntu/ %s multiverse" >> /etc/apt/sources.list' % (archive_type, distribution))
}@
RUN grep -q -F -e "deb http://old-releases.ubuntu.com" /etc/apt/sources.list && (@(' && '.join(old_releases_commands))) || (@(' && '.join(archive_commands)))
@[  elif arch in ['armhf', 'armv8']]@
@{
commands = []
for distribution, archive_type in product((os_code_name, os_code_name + '-updates', os_code_name + '-security'), ('deb', 'deb-src')):
    commands.append('echo "%s http://ports.ubuntu.com// %s multiverse" >> /etc/apt/sources.list' % (archive_type, distribution))
}@
RUN @(' && '.join(commands))
@[  end if]@
@[else if os_name == 'debian']@
# Add contrib and non-free to debian images
# Using httpredir here to match mirror used in osrf image
# (https://github.com/osrf/multiarch-docker-image-generation/blob/d251b9a/build-image.sh#L46)
RUN echo deb http://httpredir.debian.org/debian @os_code_name contrib non-free | tee -a /etc/apt/sources.list
# Hit cloudfront mirror because of corrupted packages on fastly mirrors (https://github.com/ros-infrastructure/ros_buildfarm/issues/455)
# You can remove this line to target the default mirror or replace this to use the mirror of your preference
RUN sed -i 's/httpredir.debian.org/cloudfront.debian.net/' /etc/apt/sources.list
@[end if]@
