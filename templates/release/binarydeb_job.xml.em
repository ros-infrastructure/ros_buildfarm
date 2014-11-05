<project>
	<actions/>
	<description>Generated at @ESCAPE(now_str) from template '@ESCAPE(template_name)'</description>
@(SNIPPET(
    'log-rotator',
    days_to_keep=180,
    num_to_keep=30,
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
	<scm class="hudson.scm.NullSCM"/>
	<assignedNode>buildslave</assignedNode>
	<canRoam>false</canRoam>
	<disabled>false</disabled>
	<blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
	<blockBuildWhenUpstreamBuilding>true</blockBuildWhenUpstreamBuilding>
	<triggers/>
	<concurrentBuild>false</concurrentBuild>
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
        'git clone https://github.com/ros-infrastructure/ros_buildfarm.git ros_buildfarm',
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
        '# generating the Dockerfile for the actual binarydeb task',
        'echo "# BEGIN SECTION: Generate Dockerfile - binarydeb task"',
        'mkdir -p $WORKSPACE/docker_generating_docker',
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        '$WORKSPACE/ros_buildfarm/scripts/release/run_binarydeb_job.py' +
        ' --rosdistro-index-url %s' % rosdistro_index_url +
        ' %s' % rosdistro_name +
        ' %s' % pkg_name +
        ' %s' % os_name +
        ' %s' % os_code_name +
        ' %s' % arch +
        ' ' + ' '.join(apt_mirror_args) +
        ' --binarydeb-dir $WORKSPACE/binarydeb' +
        ' --dockerfile-dir $WORKSPACE/docker_generating_docker' +
        (' --append-timestamp' if append_timestamp else ''),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - generate binarydeb"',
        'cd $WORKSPACE/docker_generating_docker',
        'docker build -t binarydeb .',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - generate binarydeb"',
        'rm -fr $WORKSPACE/binarydeb',
        'mkdir -p $WORKSPACE/binarydeb',
        'mkdir -p $WORKSPACE/docker_binarydeb',
        'docker run' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm' +
        ' -v $WORKSPACE/rosdistro:/tmp/rosdistro' +
        ' -v $WORKSPACE/binarydeb:/tmp/binarydeb' +
        ' -v $WORKSPACE/docker_binarydeb:/tmp/docker_binarydeb' +
        ' binarydeb',
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Build Dockerfile - build and upload"',
        '# build and run build_and_upload Dockerfile',
        'cd $WORKSPACE/docker_binarydeb',
        'docker build -t build_and_upload .',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - build and upload"',
        'docker run' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm' +
        ' -v $WORKSPACE/binarydeb:/tmp/binarydeb' +
        ' build_and_upload',
        'echo "# END SECTION"',
    ]),
))@
	</builders>
	<publishers>
@(SNIPPET(
    'publisher_description-setter',
    regexp="Package '[^']+' version: ([^\s]+)",
))@
@[if notify_maintainers]@
@(SNIPPET(
    'publisher_groovy-postbuild_maintainer-notification',
))@
@[end if]@
@(SNIPPET(
    'publisher_mailer',
    recipients=notify_emails,
    dynamic_recipients=maintainer_emails,
    send_to_individuals=False,
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
