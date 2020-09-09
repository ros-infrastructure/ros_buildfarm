<project>
  <actions/>
  <description>Generated at @ESCAPE(now_str) from template '@ESCAPE(template_name)'@
@[if disabled]
but disabled since the package is blacklisted (or not whitelisted) in the configuration file@
@[end if]@
@ </description>
  <keepDependencies>false</keepDependencies>
  <properties>
@(SNIPPET(
    'property_log-rotator',
    days_to_keep=730,
    num_to_keep=30,
))@
@(SNIPPET(
    'property_github-project',
    project_url=github_url,
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
    'property_parameters-definition',
    parameters=[
        {
            'type': 'boolean',
            'name': 'skip_cleanup',
            'description': 'Skip cleanup of build artifacts',
        },
    ],
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
  <disabled>@('true' if disabled else 'false')</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>true</blockBuildWhenUpstreamBuilding>
  <triggers/>
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
    os_name=os_name,
    os_code_name=os_code_name,
    arch=arch,
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
        'rm -fr $WORKSPACE/docker_sourcedeb',
        'mkdir -p $WORKSPACE/docker_sourcedeb',
        '',
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ --cid-file $WORKSPACE/docker_sourcedeb/docker.cid > $WORKSPACE/docker_sourcedeb/subprocess_reaper.log 2>&1 &',
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        '# generate Dockerfile, build and run it',
        '# generating the Dockerfile for the actual sourcedeb task',
        'echo "# BEGIN SECTION: Generate Dockerfile - sourcedeb task"',
        'export TZ="%s"' % timezone,
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/release/run_sourcedeb_job.py' +
        ' --rosdistro-index-url ' + rosdistro_index_url +
        ' ' + rosdistro_name +
        ' ' + pkg_name +
        ' ' + os_name +
        ' ' + os_code_name +
        ' ' + ' '.join(repository_args) +
        ' --source-dir $WORKSPACE/sourcedeb/source' +
        ' --dockerfile-dir $WORKSPACE/docker_sourcedeb',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - generate sourcedeb"',
        'cd $WORKSPACE/docker_sourcedeb',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build --force-rm -t sourcedeb.%s_%s_%s_%s .' % (rosdistro_name, os_name, os_code_name, pkg_name),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - generate sourcedeb"',
        'rm -fr $WORKSPACE/sourcedeb',
        'mkdir -p $WORKSPACE/sourcedeb/source',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_sourcedeb/docker.cid' +
        ' -e=TRAVIS=$TRAVIS' +
        ' --net=host' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/sourcedeb:/tmp/sourcedeb' +
        (' -v $HOME/.ssh/known_hosts:/etc/ssh/ssh_known_hosts:ro' +
         ' -v $SSH_AUTH_SOCK:/tmp/ssh_auth_sock' +
         ' -e SSH_AUTH_SOCK=/tmp/ssh_auth_sock' if git_ssh_credential_id else '') +
        ' sourcedeb.%s_%s_%s_%s' % (rosdistro_name, os_name, os_code_name, pkg_name),
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'if [ "$skip_cleanup" = "false" ]; then',
        'echo "# BEGIN SECTION: Clean up to save disk space on agents"',
        'rm -fr sourcedeb/source',
        'echo "# END SECTION"',
        'fi',
    ]),
))@
@(SNIPPET(
    'builder_publish-over-ssh',
    config_name='repo',
    remote_directory='%s/${JOB_NAME}__${BUILD_NUMBER}' % os_code_name,
    source_files=sourcedeb_files,
    remove_prefix='sourcedeb',
))@
@(SNIPPET(
    'builder_parameterized-trigger',
    project=import_package_job_name,
    parameter_files=None,
    parameters='\n'.join([
        'subfolder=%s/${JOB_NAME}__${BUILD_NUMBER}' % os_code_name,
        'debian_package_name=%s' % debian_package_name]),
    continue_on_failure=True,
))@
@(SNIPPET(
    'builder_system-groovy_check-triggered-build',
))@
  </builders>
  <publishers>
@(SNIPPET(
    'publisher_description-setter',
    regexp="Package '[^']+' version: (\S+)",
    # to prevent overwriting the description of failed builds
    regexp_for_failed='ThisRegExpShouldNeverMatch',
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
@(SNIPPET(
    'publisher_disable-failed-job',
    failure_times=5,
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
@{
credential_ids = [credential_id]
if git_ssh_credential_id:
    credential_ids.append(git_ssh_credential_id)
}@
@(SNIPPET(
    'build-wrapper_ssh-agent',
    credential_ids=credential_ids,
))@
  </buildWrappers>
</project>
