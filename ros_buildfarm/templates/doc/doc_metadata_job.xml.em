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
@[if job_priority is not None]@
@(SNIPPET(
    'property_job-priority',
    priority=job_priority,
))@
@[end if]@
@(SNIPPET(
    'property_rebuild-settings',
))@
@(SNIPPET(
    'property_requeue-job',
))@
@(SNIPPET(
    'property_job-weight',
))@
  </properties>
@(SNIPPET(
    'scm_null',
))@
  <assignedNode>@(node_label)</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers>
@(SNIPPET(
    'trigger_timer',
    spec='H 3 H/3 * *',
))@
  </triggers>
  <concurrentBuild>false</concurrentBuild>
  <builders>
@(SNIPPET(
    'builder_system-groovy_check-free-disk-space',
))@
@(SNIPPET(
    'builder_shell_docker-info',
))@
@(SNIPPET(
    'builder_check-docker',
    os_name='ubuntu',
    os_code_name='xenial',
    arch='amd64',
))@
@(SNIPPET(
    'builder_shell_clone-ros-buildfarm',
    ros_buildfarm_repository=ros_buildfarm_repository,
    wrapper_scripts=wrapper_scripts,
))@
@(SNIPPET(
    'builder_shell_key-files',
    script_generating_key_files=script_generating_key_files,
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'rm -fr $WORKSPACE/docker_doc_metadata',
        'rm -fr $WORKSPACE/generated_documentation',
        'mkdir -p $WORKSPACE/docker_doc_metadata',
        'mkdir -p $WORKSPACE/generated_documentation',
        '',
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ --cid-file $WORKSPACE/docker_doc_metadata/docker.cid > $WORKSPACE/docker_generating_docker/docker_doc_metadata.log 2>&1 &',
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        '# generate Dockerfile, build and run it',
        '# extracting metadata from released packages',
        'echo "# BEGIN SECTION: Generate Dockerfile - doc metadata task"',
        'export TZ="%s"' % timezone,
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/doc/run_doc_metadata_job.py' +
        ' ' + config_url +
        ' ' + rosdistro_name +
        ' ' + doc_build_name +
        ' ' + ' '.join(repository_args) +
        ' --dockerfile-dir $WORKSPACE/docker_doc_metadata',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - doc metadata"',
        'cd $WORKSPACE/docker_doc_metadata',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build --force-rm -t doc_metadata.%s .' % rosdistro_name,
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - doc metadata"',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_doc_metadata/docker.cid' +
        ' -e=HOME=/home/buildfarm' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/generated_documentation:/tmp/generated_documentation' +
        ' doc_metadata.%s' % rosdistro_name,
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_publish-over-ssh',
    config_name='docs',
    remote_directory=rosdistro_name,
    source_files=[
        'generated_documentation/api/**/manifest.yaml',
        'generated_documentation/api/**/stamp',
    ],
    remove_prefix='generated_documentation',
))@
  </builders>
  <publishers>
@(SNIPPET(
    'publisher_mailer',
    recipients=notify_emails,
    dynamic_recipients=[],
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
  </buildWrappers>
</project>
