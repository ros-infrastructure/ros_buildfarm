@(SNIPPET(
    'publisher_groovy-postbuild',
    script="""// CHECK SLAVE FOR LOW DISK SPACE AND DISABLE IT IF NECESSARY
import hudson.slaves.OfflineCause.ByCLI
import java.io.BufferedReader
import java.util.regex.Matcher
import java.util.regex.Pattern

pattern = Pattern.compile("ERROR: Disk Space is too low please look into it before starting a build")

r = manager.build.getLogReader()
br = new BufferedReader(r)
def line
while ((line = br.readLine()) != null) {
    matcher = pattern.matcher(line)
    if (matcher.matches()) {
        build = manager.build
        computer = build.executor.owner
        cause = new ByCLI("Disk space is too low (reported by build '" + build.fullDisplayName + "')")
        computer.setTemporarilyOffline(true, cause)
        manager.addInfoBadge("Disabled slave '" + computer.name + "' because disk space is too low")
        break
    }
}""",
))@
