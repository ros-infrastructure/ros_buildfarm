@[if 'base_image' not in locals()]@
@{
base_image = '%s:%s' % (
  vars().get('docker_base_image_override') or os_name,
  os_code_name,
)
}
@[end if]@
@# same logic as in builder_check-docker.xml.em
FROM @base_image
@[if vars().get('maintainer_name')]@
LABEL maintainer "@maintainer_name"
@[end if]@
