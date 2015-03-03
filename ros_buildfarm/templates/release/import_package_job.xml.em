<project>
  <actions/>
  <description>Generated at @ESCAPE(now_str) from template '@ESCAPE(template_name)'</description>
@(SNIPPET(
    'log-rotator',
    days_to_keep=30,
    num_to_keep=10000,
))@
  <keepDependencies>false</keepDependencies>
  <properties>
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
    'property_requeue-job',
))@
  </properties>
@(SNIPPET(
    'scm_git',
    url='https://github.com/ros-infrastructure/reprepro-updater.git',
    branch_name='refactor',
    relative_target_dir='reprepro-updater',
    refspec=None,
))@
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
        'python -u $WORKSPACE/reprepro-updater/scripts/include_folder.py --folder /var/repos/ubuntu/building/queue/$subfolder --package $debian_package_name --delete-folder --commit',
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
