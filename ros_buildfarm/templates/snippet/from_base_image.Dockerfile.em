@[if 'base_image' in locals()]@
FROM @base_image
@[else]@
@# same logic as in builder_check-docker.xml.em
FROM @docker_image_prefix:@os_code_name
@[end if]@
@[if vars().get('maintainer_name')]@
LABEL maintainer "@maintainer_name"
@[end if]@
