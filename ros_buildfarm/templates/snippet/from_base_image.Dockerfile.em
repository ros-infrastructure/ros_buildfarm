@[if os_name == 'ubuntu' and arch in ['i386', 'armhf']]@
@[if arch == 'i386']@
FROM osrf/ubuntu_32bit:@os_code_name
@[else]@
FROM osrf/ubuntu_armhf:@os_code_name
@[end if]@
@[else]@
FROM @os_name:@os_code_name
@[end if]@
