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
@(SNIPPET(
    'property_requeue-job',
))@
  </properties>
@(SNIPPET(
    'scm_null',
))@
  <assignedNode>buildslave</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>true</blockBuildWhenUpstreamBuilding>
  <triggers>
@[if upstream_projects]@
@(SNIPPET(
    'trigger_reverse-build',
    upstream_projects=upstream_projects,
))@
@[end if]@
  </triggers>
  <concurrentBuild>false</concurrentBuild>
  <builders>
@(SNIPPET(
    'builder_system-groovy_verify-upstream',
))@
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
        'git clone %s ros_buildfarm' % ros_buildfarm_url,
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
        'echo "# BEGIN SECTION: Build Dockerfile - binarydeb task"',
        'cd $WORKSPACE/docker_generating_docker',
        'docker build -t binarydeb .',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - binarydeb task"',
        'rm -fr $WORKSPACE/binarydeb',
        'mkdir -p $WORKSPACE/binarydeb',
        'mkdir -p $WORKSPACE/docker_build_binarydeb',
        'docker run' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/rosdistro:/tmp/rosdistro:ro' +
        ' -v $WORKSPACE/binarydeb:/tmp/binarydeb' +
        ' -v $WORKSPACE/docker_build_binarydeb:/tmp/docker_build_binarydeb' +
        ' binarydeb',
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Build Dockerfile - build binarydeb"',
        '# build and run build_binarydeb Dockerfile',
        'cd $WORKSPACE/docker_build_binarydeb',
        'docker build -t build_binarydeb .',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - build binarydeb"',
        'docker run' +
        ' --net=host' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/binarydeb:/tmp/binarydeb' +
        ' build_binarydeb',
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        '# generate Dockerfile, build and run it',
        '# trying to install the built binarydeb',
        'echo "# BEGIN SECTION: Generate Dockerfile - install"',
        'mkdir -p $WORKSPACE/docker_install_binarydeb',
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        '$WORKSPACE/ros_buildfarm/scripts/release/create_binarydeb_install_task_generator.py' +
        ' %s' % os_name +
        ' %s' % os_code_name +
        ' %s' % arch +
        ' ' + ' '.join(apt_mirror_args) +
        ' --binarydeb-dir $WORKSPACE/binarydeb' +
        ' --dockerfile-dir $WORKSPACE/docker_install_binarydeb',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - install"',
        'cd $WORKSPACE/docker_install_binarydeb',
        'docker build -t install_binarydeb .',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - install"',
        'docker run' +
        ' -v $WORKSPACE/binarydeb:/tmp/binarydeb:ro' +
        ' install_binarydeb',
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_publish-over-ssh',
    remote_directory='%s/${JOB_NAME}__${BUILD_NUMBER}' % os_code_name,
    source_files=binarydeb_files,
    remove_prefix='binarydeb',
))@
@(SNIPPET(
    'builder_parameterized-trigger',
    project=import_package_job_name,
    parameters='\n'.join([
        'subfolder=%s/${JOB_NAME}__${BUILD_NUMBER}' % os_code_name,
        'debian_package_name=%s' % debian_package_name]),
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
@(SNIPPET(
    'build-wrapper_timestamper',
))@
@(SNIPPET(
    'build-wrapper_ssh-agent_credential-id',
))@
  </buildWrappers>
</project>
