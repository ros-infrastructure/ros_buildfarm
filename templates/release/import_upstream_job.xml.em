<project>
  <actions/>
  <description>Generated at @ESCAPE(now_str) from template '@ESCAPE(template_name)'</description>
@(SNIPPET(
    'log-rotator',
    days_to_keep=100,
    num_to_keep=100,
))@
  <keepDependencies>false</keepDependencies>
  <properties>
@(SNIPPET(
    'property_parameters-definition',
    parameters=[
        {
            'type': 'string',
            'name': 'config_file',
            'description': 'A specific yaml file or files. If unset it defaults to aggregating all yaml files in the directory defined by upstream_config in reprepro-updater.ini',
            'default_value': None,
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
    refspec='upstream_config',
    relative_target_dir='reprepro-updater',
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
        'echo "# BEGIN SECTION: import debian packages"',
        'export PYTHONPATH=$WORKSPACE/reprepro-updater/src:$PYTHONPATH',
        'echo "# BEGIN SUBSECTION: import debian packages for ubuntu_building"',
        '$WORKSPACE/reprepro-updater/scripts/import_upstream.py ubuntu_building $config_file --commit',
        'echo "# END SUBSECTION"',
        'echo "# BEGIN SUBSECTION: import debian packages for ubuntu_testing"',
        '$WORKSPACE/reprepro-updater/scripts/import_upstream.py ubuntu_testing $config_file --commit',
        'echo "# END SUBSECTION"',
        'echo "# BEGIN SUBSECTION: import debian packages for ubuntu_main"',
        '$WORKSPACE/reprepro-updater/scripts/import_upstream.py ubuntu_main $config_file --commit',
        'echo "# END SUBSECTION"',
        'echo "# END SECTION"',
    ]),
))@
  </builders>
  <publishers>
  </publishers>
  <buildWrappers>
@(SNIPPET(
    'build-wrapper_timestamper',
))@
  </buildWrappers>
</project>
