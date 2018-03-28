@[if os_name == 'ubuntu']@
@{
from itertools import product
}@
@[  if arch in ['amd64', 'i386']]@
@{
archive_commands = []
old_releases_commands = []
for distribution, archive_type in product((os_code_name, os_code_name + '-updates', os_code_name + '-security'), ('deb', 'deb-src')):
    archive_entry = '%s http://archive.ubuntu.com/ubuntu/ %s multiverse' % (archive_type, distribution)
    old_releases_entry = '%s http://old-releases.ubuntu.com/ubuntu/ %s multiverse' % (archive_type, distribution)
    archive_commands.append('(grep -q -F -x -e "%s" /etc/apt/sources.list || echo "%s" >> /etc/apt/sources.list)' % (archive_entry, archive_entry))
    old_releases_commands.append('(grep -q -F -x -e "%s" /etc/apt/sources.list || echo "%s" >> /etc/apt/sources.list)' % (old_releases_entry, old_releases_entry))
}@
RUN grep -q -F -e "deb http://old-releases.ubuntu.com" /etc/apt/sources.list && (@(' && '.join(old_releases_commands))) || (@(' && '.join(archive_commands)))
@[  elif arch in ['armhf', 'armv8']]@
@{
commands = []
for distribution, archive_type in product((os_code_name, os_code_name + '-updates', os_code_name + '-security'), ('deb', 'deb-src')):
    entry = '%s http://ports.ubuntu.com// %s multiverse' % (archive_type, distribution)
    commands.append('(grep -q -F -x -e "%s" /etc/apt/sources.list || echo "%s" >> /etc/apt/sources.list)' % (entry, entry))
}@
RUN @(' && '.join(commands))
@[  end if]@
@[else if os_name == 'debian']@
# Add contrib and non-free to debian images
# Using httpredir here to match mirror used in osrf image
# (https://github.com/osrf/multiarch-docker-image-generation/blob/d251b9a/build-image.sh#L46)
@{
commands = []
for component in ('contrib', 'non-free'):
    entry = 'deb http://httpredir.debian.org/debian %s %s' % (os_code_name, component)
    commands.append('(grep -q -F -x -e "%s" /etc/apt/sources.list || echo "%s" >> /etc/apt/sources.list)' % (entry, entry))
}@
RUN @(' && '.join(commands))
# Hit cloudfront mirror because of corrupted packages on fastly mirrors (https://github.com/ros-infrastructure/ros_buildfarm/issues/455)
# You can remove this line to target the default mirror or replace this to use the mirror of your preference
RUN sed -i 's/httpredir.debian.org/cloudfront.debian.net/' /etc/apt/sources.list
@[end if]@
