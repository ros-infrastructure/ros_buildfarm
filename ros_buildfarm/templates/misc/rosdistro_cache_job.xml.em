<project>
  <actions/>
  <description>Generated at @ESCAPE(now_str) from template '@ESCAPE(template_name)'</description>
  <keepDependencies>false</keepDependencies>
  <properties>
@(SNIPPET(
    'property_log-rotator',
    days_to_keep=100,
    num_to_keep=1000,
))@
@(SNIPPET(
    'property_job-priority',
    priority=10,
))@
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
    'scm_git',
    url=ros_buildfarm_repository.url,
    branch_name=ros_buildfarm_repository.version or 'master',
    relative_target_dir='ros_buildfarm',
    refspec=None,
))@
  <scmCheckoutRetryCount>2</scmCheckoutRetryCount>
  <assignedNode>master</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers>
@(SNIPPET(
    'trigger_timer',
    spec='H/5 * * * *',
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
        'rm -fr $WORKSPACE/docker_generate_rosdistro_cache',
        'mkdir -p $WORKSPACE/docker_generate_rosdistro_cache',
        '',
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ --cid-file $WORKSPACE/docker_generate_rosdistro_cache/docker.cid > $WORKSPACE/docker_generate_rosdistro_cache/subprocess_reaper.log 2>&1 &',
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        '# generate Dockerfile, build and run it',
        '# generating the rosdistro cache',
        'echo "# BEGIN SECTION: Generate Dockerfile - rosdistro cache"',
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/run_rosdistro_cache_job.py' +
        ' --rosdistro-index-url ' + rosdistro_index_url +
        ' ' + rosdistro_name +
        ' ' + ' '.join(repository_args) +
        ' --dockerfile-dir $WORKSPACE/docker_generate_rosdistro_cache',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - rosdistro cache"',
        'cd $WORKSPACE/docker_generate_rosdistro_cache',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build --force-rm -t rosdistro_cache_generation .',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - rosdistro cache"',
        'rm -fr $WORKSPACE/rosdistro_cache',
        'mkdir -p $WORKSPACE/rosdistro_cache',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_generate_rosdistro_cache/docker.cid' +
        ' --net=host' +
        ' -v $WORKSPACE/rosdistro_cache:/tmp/rosdistro_cache' +
        (' -v $HOME/.ssh/known_hosts:/etc/ssh/ssh_known_hosts:ro'
         ' -v $SSH_AUTH_SOCK:/tmp/ssh_auth_sock'
         ' -e SSH_AUTH_SOCK=/tmp/ssh_auth_sock' if git_ssh_credential_id else '') +
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
    'publisher_groovy-postbuild_reconfigure-updated-packages',
    reconfigure_job_names=reconfigure_job_names,
))@
@(SNIPPET(
    'publisher_groovy-postbuild_reconfigure-updated-repositories',
    entry_type='doc',
    reconfigure_job_names=reconfigure_doc_job_names,
))@
@(SNIPPET(
    'publisher_groovy-postbuild_reconfigure-updated-repositories',
    entry_type='source',
    reconfigure_job_names=reconfigure_source_job_names,
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
@[if git_ssh_credential_id]@
@(SNIPPET(
    'build-wrapper_ssh-agent',
    credential_ids=[git_ssh_credential_id],
))@
@[end if]@
  </buildWrappers>
</project>
