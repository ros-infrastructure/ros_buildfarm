@[if os_name == 'ubuntu' and arch == 'i386']@
FROM osrf/ubuntu_32bit:@os_code_name
@[else]@
FROM @os_name:@os_code_name
@[end if]@
