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
    priority=30,
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
    branch_name='master',
    relative_target_dir='ros_buildfarm',
    refspec=None,
))@
  <assignedNode>slave_on_master</assignedNode>
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
    'builder_shell_docker-info',
))@
@(SNIPPET(
    'builder_shell_key-files',
    script_generating_key_files=script_generating_key_files,
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        '# generate Dockerfile, build and run it',
        '# generating the Dockerfiles for the actual devel tasks',
        'echo "# BEGIN SECTION: Generate Dockerfile - reconfigure jobs"',
        'mkdir -p $WORKSPACE/docker_generate_devel_jobs',
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/devel/run_devel_reconfigure_job.py' +
        ' ' + config_url +
        ' ' + rosdistro_name +
        ' ' + source_build_name +
        ' ' + ' '.join(repository_args) +
        ' --dockerfile-dir $WORKSPACE/docker_generate_devel_jobs',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - reconfigure jobs"',
        'cd $WORKSPACE/docker_generate_devel_jobs',
        'docker build -t devel_reconfigure_jobs .',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - reconfigure jobs"',
        'docker run' +
        ' --net=host' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v %s:%s:ro' % (credentials_src, credentials_dst) +
        ' devel_reconfigure_jobs',
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
@(SNIPPET(
    'build-wrapper_disk-check',
))@
  </buildWrappers>
</project>
