@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Check docker status"',
        'echo "Testing trivial docker invocation..."',
        'docker run --rm ubuntu:trusty true ; echo "\'docker run\' returned $?"',
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

println "# END SECTION"
""",
    script_file=None,
    classpath='',
))@
