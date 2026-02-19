@[if 'base_image' not in locals()]@
@{
base_image = '%s:%s' % (
  vars().get('docker_image_prefix') or (
      'osrf/%s_%s' % (os_name, arch)
      if arch in ('i386', 'armhf', 'arm64') and (
            os_code_name in (
                'artful', 'bionic', 'cosmic', 'disco', 'focal',
                'jammy', 'noble', 'wily', 'xenial', 'yakkety',
                'zesty')
      )
      else os_name
  ),
  os_code_name,
)
}
@[end if]@
@# same logic as in builder_check-docker.xml.em
FROM @base_image
@[if vars().get('maintainer_name')]@
LABEL maintainer "@maintainer_name"
@[end if]@
