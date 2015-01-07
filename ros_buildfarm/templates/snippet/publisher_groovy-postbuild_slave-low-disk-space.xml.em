@(SNIPPET(
    'publisher_groovy-postbuild',
    script="""// CHECK SLAVE FOR LOW DISK SPACE AND DISABLE IT IF NECESSARY
import hudson.node_monitors.DiskSpaceMonitor
import hudson.node_monitors.NodeMonitor
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
        // get disk space monitor
        diskSpaceMonitor = null
        for (nodeMonitor in NodeMonitor.getAll()) {
            if (nodeMonitor instanceof DiskSpaceMonitor) {
                diskSpaceMonitor = nodeMonitor
                break
            }
        }
        if (diskSpaceMonitor) {
            computer = manager.build.executor.owner
            // this implicitly disables the slave
            diskSpaceMonitor.data(computer)
            manager.addInfoBadge("Disabled slave '" + computer.name + "' because disk space is too low")
        }
        break
    }
}""",
))@
