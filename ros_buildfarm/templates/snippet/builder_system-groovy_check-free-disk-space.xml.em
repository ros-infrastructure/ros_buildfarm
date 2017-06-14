@(SNIPPET(
    'builder_system-groovy',
    command=
"""// VERFIY THAT FREE DISK SPACE THRESHOLD IS NOT VIOLATED
import hudson.model.Cause.UserIdCause
import hudson.model.ParametersAction
import hudson.node_monitors.AbstractDiskSpaceMonitor
import hudson.node_monitors.DiskSpaceMonitor
import hudson.node_monitors.DiskSpaceMonitorDescriptor.DiskSpace
import hudson.node_monitors.Messages
import hudson.node_monitors.NodeMonitor
import java.util.logging.Logger
import org.jvnet.hudson.plugins.groovypostbuild.GroovyPostbuildAction

println "# BEGIN SECTION: Check free disk space"

def node = build.getBuiltOn()
def root_path = node.getRootPath()
def usable_disk_space = root_path.getUsableDiskSpace()
println "Usable disk space = " + usable_disk_space + " bytes"

try {
  for (node_monitor in NodeMonitor.getAll()) {
    if (!(node_monitor instanceof DiskSpaceMonitor)) continue

    free_space_threshold = node_monitor.getThresholdBytes()
    println "Free space threshold = " + free_space_threshold + " bytes"

    if (usable_disk_space < free_space_threshold) {
      println "Free disk space is lower than the threshold, aborting this build, disabling the agent, rescheduling the job"

      // mark agent as offline and log event
      def computer = node.toComputer()
      def disk_space = new DiskSpace(root_path.getRemote(), usable_disk_space)
      disk_space.setTriggered(node_monitor.getClass(), true);
      if (node_monitor.getDescriptor().markOffline(computer, disk_space)) {
        def logger = Logger.getLogger(AbstractDiskSpaceMonitor.class.getName())
        logger.warning(Messages.DiskSpaceMonitor_MarkedOffline(computer.getName()))
      }

      // rescheduled a build with the same parameters
      // the requeue flag in the project configuration seems to not be sufficient anymore
      build.getProject().scheduleBuild(1, new UserIdCause(), *build.getActions(ParametersAction))

      // add badge to build
      build.getActions().add(GroovyPostbuildAction.createInfoBadge("Free disk space is too low, disabled agent '" + computer.name + "', rescheduled job"))

      // abort this build
      throw new InterruptedException()
    }
    break
  }
} finally {
  println "# END SECTION"
}
""",
    script_file=None,
))@
