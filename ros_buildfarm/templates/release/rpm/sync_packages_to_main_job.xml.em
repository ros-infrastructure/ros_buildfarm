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
    url=ros_buildfarm_repository.url,
    branch_name=ros_buildfarm_repository.version or 'master',
    relative_target_dir='ros_buildfarm',
    refspec=None,
))@
  <scmCheckoutRetryCount>2</scmCheckoutRetryCount>
  <assignedNode>building_repository</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers>
@(SNIPPET(
    'trigger_reverse-build',
    upstream_projects=[deb_sync_to_main_job_name],
))@
  </triggers>
  <concurrentBuild>false</concurrentBuild>
  <builders>
@{
target_map = {}
for os_name, os_code_name, arch in sync_targets:
    target_map.setdefault(os_name, {})
    target_map[os_name].setdefault(os_code_name, set())
    target_map[os_name][os_code_name].add(arch)
cra_sync_targets = []
for os_name, os_code_names in target_map.items():
    for os_code_name, arches in os_code_names.items():
        cra_sync_targets.append((os_name, os_code_name, rosdistro_name, arches))
}@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: sync packages to main repos"',
    ] + [
        'createrepo-agent /var/repos/%s/main/%s/ --sync=/var/repos/%s/testing/%s/ --arch=SRPMS --arch=%s --sync-pattern="ros-%s-.*" --invalidate-family' % (os_name, os_code_name, os_name, os_code_name, ' --arch='.join(arches), rosdistro_name)
        for os_name, os_code_name, rosdistro_name, arches in cra_sync_targets
    ] + [
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
