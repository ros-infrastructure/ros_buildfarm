<project>
  <actions/>
  <description>
    &lt;p&gt;
      &lt;b&gt;This job should not be aborted since reprepro will likely leave lockfiles behind!&lt;/b&gt;
    &lt;/p&gt;
Generated at @ESCAPE(now_str) from template '@ESCAPE(template_name)'</description>
  <keepDependencies>false</keepDependencies>
  <properties>
@(SNIPPET(
    'property_log-rotator',
    days_to_keep=365 * 3,
    num_to_keep=1000,
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
    'property_parameters-definition',
    parameters=[
        {
            'type': 'string',
            'name': 'config_file',
            'description': 'A specific yaml file or files to use as reprepro_config arguments. The default is the ros_bootstrap config. If unset it defaults to aggregating all yaml files in the directory defined by upstream_config in reprepro-updater.ini(not recommended)',
            'default_value': '/home/jenkins-agent/reprepro_config/ros_bootstrap.yaml',
        },
        {
            'type': 'boolean',
            'name': 'EXECUTE_IMPORT',
            'description': 'If this is not true, it will only do a dry run and print the expect import, but not execute.',
            'default_value': 'false',
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
        'echo "# BEGIN SECTION: import debian packages"',
        'if [ "$EXECUTE_IMPORT" = "true" ]; then',
        '  export COMMIT_ARG="--commit"',
        'fi',
        'export PYTHONPATH=$WORKSPACE/reprepro-updater/src:$PYTHONPATH',
        'echo "# BEGIN SUBSECTION: import debian packages for ubuntu_building"',
        'python3 -u $WORKSPACE/reprepro-updater/scripts/import_upstream.py ubuntu_building $config_file $COMMIT_ARG',
        'echo "# END SUBSECTION"',
        'echo "# BEGIN SUBSECTION: import debian packages for ubuntu_testing"',
        'python3 -u $WORKSPACE/reprepro-updater/scripts/import_upstream.py ubuntu_testing $config_file $COMMIT_ARG',
        'echo "# END SUBSECTION"',
        'echo "# BEGIN SUBSECTION: import debian packages for ubuntu_main"',
        'python3 -u $WORKSPACE/reprepro-updater/scripts/import_upstream.py ubuntu_main $config_file $COMMIT_ARG',
        'echo "# END SUBSECTION"',
        'echo "# END SECTION"',
    ]),
))@
  </builders>
  <publishers>
@(SNIPPET(
    'publisher_mailer',
    recipients=recipients,
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
