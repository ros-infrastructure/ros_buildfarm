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
    'property_job-priority',
    priority=2,
))@
	</properties>
@(SNIPPET(
    'scm_git',
    url=ros_buildfarm_url,
    refspec='master',
    relative_target_dir='ros_buildfarm',
))@
	<assignedNode>master</assignedNode>
	<canRoam>false</canRoam>
	<disabled>false</disabled>
	<blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
	<blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
	<triggers>
@(SNIPPET(
    'trigger_timer',
    spec='0 23 * * *',
))@
	</triggers>
	<concurrentBuild>false</concurrentBuild>
	<builders>
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        '# TODO remove temporary checkout of rosdistro and dependency installation',
        'echo "# BEGIN SECTION: Clone custom rosdistro"',
        'rm -fr rosdistro',
        'git clone https://github.com/dirk-thomas/ros-infrastructure_rosdistro.git rosdistro',
        'export PYTHONPATH=$WORKSPACE/rosdistro/src:$PYTHONPATH',
        'echo "# END SECTION"',
        '',
        'cd ros_buildfarm',
        'export PYTHONPATH=`pwd`:$PYTHONPATH',
        'python3 -u scripts/devel/generate_devel_jobs.py ' +
        '--rosdistro-index-url "%s" %s %s' % (rosdistro_index_url, rosdistro_name, source_build_name),
    ]),
))@
	</builders>
	<publishers>
@(SNIPPET(
    'publisher_mailer',
    recipients=recipients,
    send_to_individuals=False,
))@
	</publishers>
	<buildWrappers/>
</project>
