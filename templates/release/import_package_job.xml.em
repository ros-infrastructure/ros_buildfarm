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
            'name': 'subfolder',
            'description': '',
            'default_value': None,
        },
        {
            'type': 'string',
            'name': 'debian_package_name',
            'description': '',
            'default_value': None,
        },
    ],
))@
	</properties>
@(SNIPPET(
    'scm_git',
    url='https://github.com/ros-infrastructure/reprepro-updater.git',
    refspec='refactor',
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
        'echo "# BEGIN SECTION: import debian package"',
        'export PYTHONPATH=$WORKSPACE/reprepro-updater/src:$PYTHONPATH',
        '$WORKSPACE/reprepro-updater/scripts/include_folder.py --folder /var/repos/ubuntu/building/queue/$subfolder --package $debian_package_name --delete-folder --commit',
        'echo "# END SECTION"',
    ]),
))@
	</builders>
	<publishers>
@(SNIPPET(
    'publisher_description-setter',
    regexp="Imported package: ([^\s]+)",
))@
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
