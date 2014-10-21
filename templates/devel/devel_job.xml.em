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
@[if job_priority is not None]@
@(SNIPPET(
    'property_job-priority',
    priority=job_priority,
))@
@[end if]@
	</properties>
@(SNIPPET(
    'scm',
    repo_spec=source_repo_spec,
    path='catkin_workspace/src/%s' % source_repo_spec.name
))@
	<assignedNode>buildslave</assignedNode>
	<canRoam>false</canRoam>
	<disabled>false</disabled>
	<blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
	<blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
	<triggers>
@(SNIPPET(
    'trigger_poll',
    spec='H * * * *',
))@
	</triggers>
	<concurrentBuild>true</concurrentBuild>
	<builders>
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Clone custom rosdistro"',
        'rm -fr rosdistro',
        'git clone https://github.com/dirk-thomas/ros-infrastructure_rosdistro.git rosdistro',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Clone ros_buildfarm"',
        'rm -fr ros_buildfarm',
        'git clone https://github.com/dirk-thomas/ros_buildfarm.git ros_buildfarm',
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        '# generate key files',
        'echo "# BEGIN SECTION: Generate key files"',
    ] + script_generating_key_files + [
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        '# generate Dockerfile, build and run it',
        '# generating the Dockerfiles for the actual build tasks',
        'echo "# BEGIN SECTION: Generate Dockerfile 1"',
        'mkdir -p $WORKSPACE/docker_generating_devel_dockers',
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        '$WORKSPACE/ros_buildfarm/scripts/devel/run_devel_job.py' +
        ' --rosdistro-index-url %s' % rosdistro_index_url +
        ' --rosdistro-name %s' % rosdistro_name +
        ' --source-build-name %s' % source_build_name +
        ' --repo-name %s' % source_repo_spec.name +
        ' --os-name %s' % os_name +
        ' --os-code-name %s' % os_code_name +
        ' --arch %s' % arch +
        ' ' + ' '.join(apt_mirror_args) +
        ' --workspace-root $WORKSPACE/catkin_workspace' +
        ' --dockerfile-dir $WORKSPACE/docker_generating_devel_dockers',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - generating docker tasks"',
        'cd $WORKSPACE/docker_generating_devel_dockers',
        'docker build -t devel .',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - generating docker tasks"',
        'mkdir -p $WORKSPACE/docker_build_and_install',
        'mkdir -p $WORKSPACE/docker_build_and_test',
        'docker run' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm' +
        ' -v $WORKSPACE/catkin_workspace:/tmp/catkin_workspace' +
        ' -v $WORKSPACE/docker_build_and_install:/tmp/docker_build_and_install' +
        ' -v $WORKSPACE/docker_build_and_test:/tmp/docker_build_and_test' +
        ' devel',
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Build Dockerfile - build and install"',
        '# build and run build_and_install Dockerfile',
        'cd $WORKSPACE/docker_build_and_install',
        'docker build -t build_and_install .',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - build and install"',
        'docker run' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm' +
        ' -v $WORKSPACE/catkin_workspace:/tmp/catkin_workspace' +
        ' build_and_install',
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Build Dockerfile - build and test"',
        '# build and run build_and_test Dockerfile',
        'cd $WORKSPACE/docker_build_and_test',
        'docker build -t build_and_test .',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - build and test"',
        'docker run' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm' +
        ' -v $WORKSPACE/catkin_workspace:/tmp/catkin_workspace' +
        ' build_and_test',
        'echo "# END SECTION"',
    ]),
))@
	</builders>
	<publishers>
@(SNIPPET(
    'publisher_junit',
    test_results='catkin_workspace/build_isolated/**/*.xml',
))@
@(SNIPPET(
    'publisher_mailer',
    recipients=recipients,
    send_to_individuals=True,
))@
	</publishers>
	<buildWrappers>
@[if timeout_minutes is not None]@
@(SNIPPET(
    'build-wrapper_build-timeout',
    timeout_minutes=timeout_minutes,
))@
@[end if]@
	</buildWrappers>
</project>
