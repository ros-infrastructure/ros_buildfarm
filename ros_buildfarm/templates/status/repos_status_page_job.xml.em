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
    priority=20,
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
  <assignedNode>agent_on_master||buildagent</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers>
@(SNIPPET(
    'trigger_timer',
    spec='H * * * *',
))@
  </triggers>
  <concurrentBuild>false</concurrentBuild>
  <builders>
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'rm -fr $WORKSPACE/package_repo_cache',
        'rm -fr $WORKSPACE/status_page',
        'mkdir -p $WORKSPACE/package_repo_cache',
        'mkdir -p $WORKSPACE/status_page',
    ]),
))@
@[for status_page_name in sorted(status_pages.keys())]@
@{
status_page = status_pages[status_page_name]
debian_repository_urls = status_page['debian_repository_urls']
os_name_and_os_code_name_and_arch_tuples = status_page['os_name_and_os_code_name_and_arch_tuples']
}@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: generate repos status page: %s"' % status_page_name,
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/status/build_repos_status_page.py' +
        ' ' + rosdistro_name +
        ' ' + ' '.join(debian_repository_urls) +
        ' --os-name-and-os-code-name-and-arch-tuples ' +
        ' '.join(os_name_and_os_code_name_and_arch_tuples) +
        ' --cache-dir $WORKSPACE/package_repo_cache' +
        ' --output-name %s_%s' % (rosdistro_name, status_page_name) +
        ' --output-dir $WORKSPACE/status_page',
        'echo "# END SECTION"',
    ]),
))@
@[end for]@
  </builders>
  <publishers>
@(SNIPPET(
    'publisher_publish-over-ssh',
    config_name='status_page',
    remote_directory='',
    source_files=['status_page/**'],
    remove_prefix='status_page',
))@
@(SNIPPET(
    'publisher_mailer',
    recipients=notification_emails,
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
