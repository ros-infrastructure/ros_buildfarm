<project>
  <actions/>
  <description>Generated at @ESCAPE(now_str) from template '@ESCAPE(template_name)'</description>
  <keepDependencies>false</keepDependencies>
  <properties>
@(SNIPPET(
    'property_log-rotator',
    days_to_keep=100,
    num_to_keep=100,
))@
@(SNIPPET(
    'property_job-priority',
    priority=-1,
))@
@(SNIPPET(
    'property_rebuild-settings',
))@
@(SNIPPET(
    'property_requeue-job',
))@
@(SNIPPET(
    'property_job-weight',
))@
  </properties>
@(SNIPPET(
    'scm_git',
    url='https://github.com/ros-infrastructure/reprepro-updater.git',
    branch_name='refactor',
    relative_target_dir='reprepro-updater',
    refspec=None,
))@
  <scmCheckoutRetryCount>2</scmCheckoutRetryCount>
  <assignedNode>building_repository</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
@{
sync_to_testing_jobs_groovy = ', '.join(
    "'" + n + "'" for n in sync_to_testing_job_names)
check_sync_to_testing_command = """\
import hudson.model.Result

println ""
println "# BEGIN SECTION: Check upstream sync-to-testing jobs"
println "Verify that no sync-to-testing job is in progress or broken:"
println ""

def syncToTestingJobs = [%s]
def jenkins = Jenkins.instance
def allGood = true

for (jobName in syncToTestingJobs) {
  def job = jenkins.getItemByFullName(jobName)
  if (job == null) {
    println "  - '" + jobName + "' not found"
    allGood = false
    continue
  }
  if (job.isBuilding()) {
    println "  - '" + jobName + "' is currently building"
    allGood = false
    continue
  }
  if (job.isInQueue()) {
    println "  - '" + jobName + "' is currently queued"
    allGood = false
    continue
  }
  if (job.getNextBuildNumber() == 1) {
    println "  - '" + jobName + "' has not been built yet"
    allGood = false
    continue
  }
  def lb = job.getLastBuild()
  if (lb == null) {
    println "  - '" + jobName + "' can't provide last build"
    allGood = false
    continue
  }
  def r = lb.getResult()
  if (r == null || r.isWorseOrEqualTo(Result.FAILURE)) {
    println "  - '" + jobName + "' build '" + lb.getNumber() + "' has result '" + r + "'"
    allGood = false
    continue
  }
  println "  - '" + jobName + "' build '" + lb.getNumber() + "' has result '" + r + "'"
}

if (!allGood) {
  println ""
  println "  -> aborting build"
  throw new InterruptedException()
}
println "All sync-to-testing jobs are (un)stable"
println ""
println "# END SECTION"
""" % sync_to_testing_jobs_groovy
}@
@(SNIPPET(
    'builder_system-groovy',
    command=check_sync_to_testing_command,
    script_file=None,
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: sync packages to main repo"',
        'export PYTHONPATH=$WORKSPACE/reprepro-updater/src:$PYTHONPATH',
        'python3 -u $WORKSPACE/reprepro-updater/scripts/sync_ros_packages.py ubuntu_main --upstream-ros ubuntu_testing -r %s -c' % rosdistro_name,
        'echo "# END SECTION"',
    ]),
))@
  </builders>
  <publishers>
@(SNIPPET(
    'publisher_mailer',
    recipients=notify_emails,
    dynamic_recipients=[],
    send_to_individuals=False,
))@
  </publishers>
  <buildWrappers>
@(SNIPPET(
    'build-wrapper_timestamper',
))@
  </buildWrappers>
</project>
