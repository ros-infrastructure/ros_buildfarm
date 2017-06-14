@(SNIPPET(
    'builder_system-groovy',
    command=
"""// CHECK FREE DISK SPACE OF DISABLED SLAVES
import hudson.node_monitors.DiskSpaceMonitor
import hudson.node_monitors.DiskSpaceMonitorDescriptor.DiskSpace
import hudson.node_monitors.NodeMonitor

import jenkins.model.Jenkins

println "Checking free disk space of all offline computers..."

for (computer in Jenkins.instance.getComputers()) {
  if (!computer.isOffline()) continue
  println "- checking offline computer '" + computer.getName() + "'"

  for (node_monitor in NodeMonitor.getAll()) {
    if (!(node_monitor instanceof DiskSpaceMonitor)) continue

    DiskSpace size = (DiskSpace)node_monitor.data(computer)
    if (size != null) {
      println "  free disk space = " + size.size
      if (!computer.isOffline()) {
        println "  reenabled"
      }
    }
    break
  }
}
""",
    script_file=None,
))@
