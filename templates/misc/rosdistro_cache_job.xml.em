<project>
  <actions/>
  <description>Generated at @ESCAPE(now_str) from template '@ESCAPE(template_name)'</description>
@(SNIPPET(
    'log-rotator',
    days_to_keep=100,
    num_to_keep=1000,
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
    spec='*/5 * * * *',
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
        '# generating the rosdistro cache',
        'echo "# BEGIN SECTION: Generate Dockerfile - rosdistro cache"',
        'mkdir -p $WORKSPACE/docker_generate_rosdistro_cache',
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        '$WORKSPACE/ros_buildfarm/scripts/misc/run_rosdistro_cache_job.py' +
        ' --rosdistro-index-url ' + rosdistro_index_url +
        ' ' + rosdistro_name +
        ' ' + ' '.join(repository_args) +
        ' --dockerfile-dir $WORKSPACE/docker_generate_rosdistro_cache',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - rosdistro cache"',
        'cd $WORKSPACE/docker_generate_rosdistro_cache',
        'docker build -t rosdistro_cache_generation .',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - rosdistro cache"',
        'rm -fr $WORKSPACE/rosdistro_cache',
        'mkdir -p $WORKSPACE/rosdistro_cache',
        'docker run' +
        ' --net=host' +
        ' -v $WORKSPACE/rosdistro:/tmp/rosdistro:ro' +
        ' -v $WORKSPACE/rosdistro_cache:/tmp/rosdistro_cache' +
        ' rosdistro_cache_generation',
        'echo "# END SECTION"',
    ]),
))@
  </builders>
  <publishers>
@(SNIPPET(
    'publisher_publish-over-ssh',
    config_name='rosdistro_cache',
    remote_directory='',
    source_files=['rosdistro_cache/*.gz'],
    remove_prefix='rosdistro_cache',
))@
@(SNIPPET(
    'publisher_mailer',
    recipients=notification_emails,
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
