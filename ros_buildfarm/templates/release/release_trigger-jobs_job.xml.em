<project>
  <actions/>
  <description>Generated at @ESCAPE(now_str) from template '@ESCAPE(template_name)'</description>
  <keepDependencies>false</keepDependencies>
  <properties>
@(SNIPPET(
    'property_log-rotator',
    days_to_keep=365,
    num_to_keep=100,
))@
@(SNIPPET(
    'property_job-priority',
    priority=40,
))@
@(SNIPPET(
    'property_requeue-job',
))@
    <hudson.model.ParametersDefinitionProperty>
      <parameterDefinitions>
        <hudson.model.ChoiceParameterDefinition>
          <name>args</name>
          <description/>
          <choices class="java.util.Arrays$ArrayList">
            <a class="string-array">
              <string>--missing-only --source-only</string>
              <string>--missing-only</string>
              <string>--source-only</string>
              <string> </string>
            </a>
          </choices>
        </hudson.model.ChoiceParameterDefinition>
      </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
  </properties>
@(SNIPPET(
    'scm_git',
    url=ros_buildfarm_repository.url,
    branch_name=ros_buildfarm_repository.version or 'master',
    relative_target_dir='ros_buildfarm',
    refspec=None,
))@
  <scmCheckoutRetryCount>2</scmCheckoutRetryCount>
  <assignedNode>slave_on_master</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers>
@(SNIPPET(
    'trigger_timer',
    spec='*/15 * * * *',
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
        'rm -fr $WORKSPACE/docker_trigger_jobs',
        'rm -fr $WORKSPACE/trigger_jobs',
        'mkdir -p $WORKSPACE/docker_trigger_jobs',
        'mkdir -p $WORKSPACE/trigger_jobs',
        '',
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ --cid-file $WORKSPACE/docker_trigger_jobs/docker.cid > $WORKSPACE/docker_trigger_jobs/subprocess_reaper.log 2>&1 &',
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        '# generate Dockerfile, build and run it',
        '# generating the Dockerfiles for the actual trigger jobs tasks',
        'echo "# BEGIN SECTION: Generate Dockerfile - trigger jobs"',
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/release/run_trigger_job.py' +
        ' ' + config_url +
        ' ' + rosdistro_name +
        ' ' + release_build_name +
        ' ' + ' '.join(repository_args) +
        ' $args' +
        ' --groovy-script /tmp/trigger_jobs/trigger_jobs.groovy' +
        ' --cache-dir /tmp/debian_repo_cache' +
        ' --dockerfile-dir $WORKSPACE/docker_trigger_jobs',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - trigger jobs"',
        'cd $WORKSPACE/docker_trigger_jobs',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build --force-rm -t release_trigger_jobs .',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - trigger jobs"',
        'rm -fr $WORKSPACE/debian_repo_cache',
        'mkdir -p $WORKSPACE/debian_repo_cache',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_trigger_jobs/docker.cid' +
        ' --net=host' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v %s:%s:ro' % (credentials_src, credentials_dst) +
        ' -v $WORKSPACE/trigger_jobs:/tmp/trigger_jobs' +
        ' -v $WORKSPACE/debian_repo_cache:/tmp/debian_repo_cache' +
        ' release_trigger_jobs',
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_system-groovy',
    command=None,
    script_file='$WORKSPACE/trigger_jobs/trigger_jobs.groovy',
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
