<project>
  <actions/>
  <description>Generated at @ESCAPE(now_str) from template '@ESCAPE(template_name)'</description>
  <keepDependencies>false</keepDependencies>
  <properties>
@(SNIPPET(
    'property_log-rotator',
    days_to_keep=30,
    num_to_keep=10000,
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
    'property_parameters-definition',
    parameters=[
        {
            'type': 'string',
            'name': 'subfolder',
        },
        {
            'type': 'string',
            'name': 'debian_package_name',
        },
    ],
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
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: import debian package"',
        'export PYTHONPATH=$WORKSPACE/reprepro-updater/src:$PYTHONPATH',
        'python3 -u $WORKSPACE/reprepro-updater/scripts/include_folder.py --folder ' + (target_queue if target_queue else '/var/repos/ubuntu/building/queue') + '/$subfolder --package $debian_package_name --delete-folder --commit' + (' --invalidate' if abi_incompatibility_assumed else ''),
        'echo "# END SECTION"',
    ]),
))@
  </builders>
  <publishers>
@(SNIPPET(
    'publisher_description-setter',
    regexp='Importing package: (\S+)',
    # to prevent overwriting the description of failed builds
    regexp_for_failed='ThisRegExpShouldNeverMatch',
))@
@(SNIPPET(
    'publisher_extended-email',
    recipients=notify_emails,
))@
  </publishers>
  <buildWrappers>
@(SNIPPET(
    'build-wrapper_timestamper',
))@
  </buildWrappers>
</project>
