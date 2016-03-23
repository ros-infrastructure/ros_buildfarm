@[if arch in ['i386', 'armhf', 'arm64']]@
FROM osrf/@(os_name)_@arch:@os_code_name
@[else]@
FROM @os_name:@os_code_name
@[end if]@
