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
  </properties>
@(SNIPPET(
    'scm_git',
    url=ros_buildfarm_repository.url,
    branch_name=ros_buildfarm_repository.version or 'master',
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
    script="""rm -fr $WORKSPACE/classpath
mkdir -p $WORKSPACE/classpath
cd $WORKSPACE/classpath
wget https://java-diff-utils.googlecode.com/files/diffutils-1.2.1.jar""",
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'rm -fr $WORKSPACE/docker_generate_devel_jobs',
        'rm -fr $WORKSPACE/reconfigure_jobs',
        'mkdir -p $WORKSPACE/docker_generate_devel_jobs',
        'mkdir -p $WORKSPACE/reconfigure_jobs',
        '',
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ --cid-file $WORKSPACE/docker_generate_devel_jobs/docker.cid > $WORKSPACE/docker_generate_devel_jobs/subprocess_reaper.log 2>&1 &',
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        '# generate Dockerfile, build and run it',
        '# generating the Dockerfiles for the actual devel tasks',
        'echo "# BEGIN SECTION: Generate Dockerfile - reconfigure jobs"',
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/devel/run_devel_reconfigure_job.py' +
        ' ' + config_url +
        ' ' + rosdistro_name +
        ' ' + source_build_name +
        ' ' + ' '.join(repository_args) +
        ' --groovy-script /tmp/reconfigure_jobs/reconfigure_jobs.groovy' +
        ' --dockerfile-dir $WORKSPACE/docker_generate_devel_jobs',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - reconfigure jobs"',
        'cd $WORKSPACE/docker_generate_devel_jobs',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build -t devel_reconfigure_jobs .',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - reconfigure jobs"',
        'docker run' +
        ' --cidfile=$WORKSPACE/docker_generate_devel_jobs/docker.cid' +
        ' --net=host' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v %s:%s:ro' % (credentials_src, credentials_dst) +
        ' -v $WORKSPACE/reconfigure_jobs:/tmp/reconfigure_jobs' +
        ' devel_reconfigure_jobs',
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_system-groovy',
    command=None,
    script_file='$WORKSPACE/reconfigure_jobs/reconfigure_jobs.groovy',
    classpath='$WORKSPACE/classpath/diffutils-1.2.1.jar',
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
