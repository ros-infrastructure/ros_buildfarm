@[if 'base_image' in locals()]@
FROM @base_image
@[else]@
@# same logic as in builder_check-docker.xml.em
@[  if arch in ['i386', 'armhf', 'arm64']]@
FROM osrf/@(os_name)_@arch:@os_code_name
@[  else]@
FROM @os_name:@os_code_name
@[  end if]@
@[end if]@
@[if vars().get('maintainer_name')]@
LABEL maintainer "@maintainer_name"
@[end if]@
