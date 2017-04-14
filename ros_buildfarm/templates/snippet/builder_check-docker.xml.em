@{
# same logic as in from_base_image.Dockerfile.em
if arch in ['i386', 'armhf', 'arm64']:
    base_image = 'osrf/%s_%s:%s' % (os_name, arch, os_code_name)
else:
    base_image = '%s:%s' % (os_name, os_code_name)
}@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Check docker status"',
        'echo "Testing trivial docker invocation..."',
        'docker run --rm %s true ; echo "\'docker run\' returned $?"' % base_image,
    ]),
))@
@(SNIPPET(
    'builder_system-groovy',
    command=
"""// DISABLE SLAVE IF OUTPUT INDICATES DOCKER RUN PROBLEMS
import hudson.slaves.OfflineCause.UserCause
import java.io.BufferedReader
import java.util.regex.Pattern
import org.jvnet.hudson.plugins.groovypostbuild.GroovyPostbuildAction

pattern = Pattern.compile("'docker run' returned [^0].*")

r = build.getLogReader()
br = new BufferedReader(r)
def line
while ((line = br.readLine()) != null) {
    matcher = pattern.matcher(line)
    if (matcher.matches()) {
        println "'docker run' failed"

        // mark slave as offline and log event
        def node = build.getBuiltOn()
        def computer = node.toComputer()
        computer.setTemporarilyOffline(true, new UserCause(null, "'docker run' failed"))

        // the job will be rescheduled automatically if it has corresponding flag set in the project configuration

        // add badge to build
        build.getActions().add(GroovyPostbuildAction.createInfoBadge("'docker run' failed, disabled slave '" + computer.name + "', rescheduled job"))

        // abort this build
        throw new InterruptedException()
    }
}
println "docker seems operational, continuing"
""",
    script_file=None,
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# END SECTION"',
    ]),
))@
