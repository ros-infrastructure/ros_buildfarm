@[if os_name == 'ubuntu' and arch in ['i386', 'armhf', 'arm64']]@
@[if arch == 'i386']@
FROM osrf/ubuntu_32bit:@os_code_name
@[else]@
FROM osrf/ubuntu_@arch:@os_code_name
@[end if]@
@[else]@
FROM @os_name:@os_code_name
@[end if]@
