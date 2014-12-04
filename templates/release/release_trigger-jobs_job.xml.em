<project>
  <actions/>
  <description>Generated at @ESCAPE(now_str) from template '@ESCAPE(template_name)'</description>
@(SNIPPET(
    'log-rotator',
    days_to_keep=365,
    num_to_keep=100,
))@
  <keepDependencies>false</keepDependencies>
  <properties>
@(SNIPPET(
    'property_job-priority',
    priority=2,
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
              <string></string>
              </a>
          </choices>
        </hudson.model.ChoiceParameterDefinition>
        </parameterDefinitions>
    </hudson.model.ParametersDefinitionProperty>
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
    spec='*/15 * * * *',
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
        '# generating the Dockerfiles for the actual trigger jobs tasks',
        'echo "# BEGIN SECTION: Generate Dockerfile - trigger jobs"',
        'mkdir -p $WORKSPACE/docker_trigger_jobs',
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/release/run_trigger_job.py' +
        ' ' + config_url +
        ' ' + rosdistro_name +
        ' ' + release_build_name +
        ' ' + ' '.join(repository_args) +
        ' $args' +
        ' --cache-dir /tmp/debian_repo_cache' +
        ' --dockerfile-dir $WORKSPACE/docker_trigger_jobs',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - reconfigure jobs"',
        'cd $WORKSPACE/docker_trigger_jobs',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/wrapper/docker_build.py -t release_trigger_jobs .',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - reconfigure jobs"',
        'rm -fr $WORKSPACE/debian_repo_cache',
        'mkdir -p $WORKSPACE/debian_repo_cache',
        'docker run' +
        ' --net=host' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/rosdistro:/tmp/rosdistro:ro' +
        ' -v %s:%s:ro' % (credentials_src, credentials_dst) +
        ' -v $WORKSPACE/debian_repo_cache:/tmp/debian_repo_cache' +
        ' release_trigger_jobs',
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
