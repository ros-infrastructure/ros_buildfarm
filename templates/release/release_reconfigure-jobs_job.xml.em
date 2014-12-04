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
@(SNIPPET(
    'property_requeue-job',
))@
@(SNIPPET(
    'property_disk-usage',
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
    'builder_shell_key-files',
    script_generating_key_files=script_generating_key_files,
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        '# TODO replace with python3-rosdistro',
        'echo "# BEGIN SECTION: Clone custom rosdistro"',
        'rm -fr rosdistro',
        'git clone -b rep143 https://github.com/ros-infrastructure/rosdistro.git rosdistro',
        'echo "# END SECTION"',
        '',
        '# generate Dockerfile, build and run it',
        '# generating the Dockerfiles for the actual release tasks',
        'echo "# BEGIN SECTION: Generate Dockerfile - reconfigure jobs"',
        'mkdir -p $WORKSPACE/docker_generate_release_jobs',
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/release/run_release_reconfigure_job.py' +
        ' ' + config_url +
        ' ' + rosdistro_name +
        ' ' + release_build_name +
        ' ' + ' '.join(repository_args) +
        ' --dockerfile-dir $WORKSPACE/docker_generate_release_jobs',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - reconfigure jobs"',
        'cd $WORKSPACE/docker_generate_release_jobs',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/wrapper/docker_build.py -t release_reconfigure_jobs .',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - reconfigure jobs"',
        'docker run' +
        ' --net=host' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/rosdistro:/tmp/rosdistro:ro' +
        ' -v %s:%s:ro' % (credentials_src, credentials_dst) +
        ' release_reconfigure_jobs',
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
