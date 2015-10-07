@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Clone ros_buildfarm"',
        'rm -fr ros_buildfarm',
        'git clone --depth 1 %s%s ros_buildfarm' % ('-b %s ' % ros_buildfarm_repository.version if ros_buildfarm_repository.version else '', ros_buildfarm_repository.url),
        'git -C ros_buildfarm log -n 1',
        'rm -fr ros_buildfarm/.git',
        'rm -fr ros_buildfarm/doc',
        'echo "# END SECTION"',
    ]),
))@
