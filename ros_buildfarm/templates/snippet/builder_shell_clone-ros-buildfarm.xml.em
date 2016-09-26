@{
filename = 'git.py'
wrapper_script = wrapper_scripts[filename]
# depending on the shell echo might not expand the escaped newlines
cmd = 'printf "%s" > wrapper_scripts/%s' % ('\\n'.join(wrapper_script.replace('\\', '\\\\\\\\').replace('"', '\\"').replace('%', '%%').splitlines()), filename)
}@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Embed wrapper scripts"',
        'rm -fr wrapper_scripts',
        'mkdir wrapper_scripts',
        cmd,
        'echo "# END SECTION"',
    ]),
))@
@{
import re
cmds = []
if ros_buildfarm_repository.version and re.match('[0-9a-f]{40}', ros_buildfarm_repository.version):
    # cannot create a shallow clone for hashes
    cmds += [
        'python3 -u wrapper_scripts/git.py clone %s ros_buildfarm' % ros_buildfarm_repository.url,
        'git -C ros_buildfarm checkout %s' % ros_buildfarm_repository.version,
    ]
else:
    # shallow clone when version is a branch or tag
    cmds.append('python3 -u wrapper_scripts/git.py clone --depth 1 %s%s ros_buildfarm' % ('-b %s ' % ros_buildfarm_repository.version if ros_buildfarm_repository.version else '', ros_buildfarm_repository.url))
}@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Clone ros_buildfarm"',
        'rm -fr ros_buildfarm',
    ] + cmds + [
        'git -C ros_buildfarm --no-pager log -n 1',
        'rm -fr ros_buildfarm/.git',
        'rm -fr ros_buildfarm/doc',
        'echo "# END SECTION"',
    ]),
))@
