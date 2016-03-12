@[if os_name == 'ubuntu' and arch in ['i386', 'armhf', 'arm64']]@
FROM osrf/ubuntu_@arch:@os_code_name
@[else]@
FROM @os_name:@os_code_name
@[end if]@
