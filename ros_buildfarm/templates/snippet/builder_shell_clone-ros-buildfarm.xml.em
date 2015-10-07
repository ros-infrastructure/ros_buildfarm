@{
import re
cmds = []
if ros_buildfarm_repository.version and re.match('[0-9a-f]{40}', ros_buildfarm_repository.version):
    # cannot create a shallow clone for hashes
    cmds += [
        'git clone %s ros_buildfarm' % ros_buildfarm_repository.url,
        'git -C ros_buildfarm checkout %s' % ros_buildfarm_repository.version,
    ]
else:
    # shallow clone when version is a branch or tag
    cmds.append('git clone --depth 1 %s%s ros_buildfarm' % ('-b %s ' % ros_buildfarm_repository.version if ros_buildfarm_repository.version else '', ros_buildfarm_repository.url))
}@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Clone ros_buildfarm"',
        'rm -fr ros_buildfarm',
    ] + cmds + [
        'git -C ros_buildfarm log -n 1',
        'rm -fr ros_buildfarm/.git',
        'rm -fr ros_buildfarm/doc',
        'echo "# END SECTION"',
    ]),
))@
