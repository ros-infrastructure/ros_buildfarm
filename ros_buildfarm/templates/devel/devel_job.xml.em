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
    num_to_keep=100,
))@
@[if github_url]@
@(SNIPPET(
    'property_github-project',
    project_url=github_url,
))@
@[end if]@
@[if job_priority is not None]@
@(SNIPPET(
    'property_job-priority',
    priority=job_priority,
))@
@[end if]@
@(SNIPPET(
    'property_requeue-job',
))@
@{
parameters = [
    {
        'type': 'boolean',
        'name': 'skip_cleanup',
        'description': 'Skip cleanup of catkin build artifacts as well as rosdoc index',
    },
]
if pull_request:
    parameters += [
        {
            'type': 'string',
            'name': 'sha1',
        },
    ]
}@
@(SNIPPET(
    'property_parameters-definition',
    parameters=parameters,
))@
  </properties>
@[if not pull_request]@
@(SNIPPET(
    'scm',
    repo_spec=source_repo_spec,
    path='catkin_workspace/src/%s' % source_repo_spec.name,
    git_ssh_credential_id=git_ssh_credential_id,
))@
@[else]@
@(SNIPPET(
    'scm_git',
    url=source_repo_spec.url,
    refspec='+refs/pull/*:refs/remotes/origin/pr/*',
    branch_name='${sha1}',
    relative_target_dir='catkin_workspace/src/%s' % source_repo_spec.name,
    git_ssh_credential_id=git_ssh_credential_id,
    merge_branch=source_repo_spec.version,
))@
@[end if]@
  <scmCheckoutRetryCount>2</scmCheckoutRetryCount>
  <assignedNode>@(node_label)</assignedNode>
  <canRoam>false</canRoam>
  <disabled>@('true' if disabled else 'false')</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers>
@[if not pull_request]@
@(SNIPPET(
    'trigger_poll',
    spec='H * * * *',
))@
@[end if]@
@[if pull_request]@
@(SNIPPET(
    'trigger_github-pull-request-builder',
    github_orgunit=github_orgunit,
    branch_name=source_repo_spec.version,
    job_name=job_name,
))@
@[end if]@
  </triggers>
  <concurrentBuild>true</concurrentBuild>
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
        'rm -fr $WORKSPACE/docker_generating_dockers',
        'mkdir -p $WORKSPACE/docker_generating_dockers',
        '',
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ --cid-file $WORKSPACE/docker_generating_dockers/docker.cid > $WORKSPACE/docker_generating_dockers/subprocess_reaper.log 2>&1 &',
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        '# generate Dockerfile, build and run it',
        '# generating the Dockerfiles for the actual devel tasks',
        'echo "# BEGIN SECTION: Generate Dockerfile - devel tasks"',
        'export TZ="%s"' % timezone,
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/devel/run_devel_job.py' +
        ' --rosdistro-index-url ' + rosdistro_index_url +
        ' ' + rosdistro_name +
        ' ' + source_build_name +
        ' ' + source_repo_spec.name +
        ' ' + os_name +
        ' ' + os_code_name +
        ' ' + arch +
        ' ' + ' '.join(repository_args) +
        ' --dockerfile-dir $WORKSPACE/docker_generating_dockers',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - generating devel tasks"',
        'cd $WORKSPACE/docker_generating_dockers',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build --force-rm -t devel_task_generation.%s_%s .' % (rosdistro_name, source_repo_spec.name.lower()),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - generating devel tasks"',
        'rm -fr $WORKSPACE/docker_build_and_install',
        'rm -fr $WORKSPACE/docker_build_and_test',
        'mkdir -p $WORKSPACE/docker_build_and_install',
        'mkdir -p $WORKSPACE/docker_build_and_test',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_generating_dockers/docker.cid' +
        ' -e=HOME=/home/buildfarm' +
        ' -e=TRAVIS=$TRAVIS' +
        ' -e=ROS_BUILDFARM_PULL_REQUEST_BRANCH=$ROS_BUILDFARM_PULL_REQUEST_BRANCH' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/catkin_workspace:/tmp/catkin_workspace:ro' +
        ' -v $WORKSPACE/docker_build_and_install:/tmp/docker_build_and_install' +
        ' -v $WORKSPACE/docker_build_and_test:/tmp/docker_build_and_test' +
        ' -v ~/.ccache:/home/buildfarm/.ccache' +
        (' -v $HOME/.ssh/known_hosts:/etc/ssh/ssh_known_hosts:ro' +
         ' -v $SSH_AUTH_SOCK:/tmp/ssh_auth_sock' +
         ' -e SSH_AUTH_SOCK=/tmp/ssh_auth_sock' if git_ssh_credential_id else '') +
        ' devel_task_generation.%s_%s' % (rosdistro_name, source_repo_spec.name.lower()),
        'cd -',  # restore pwd when used in scripts
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ --cid-file $WORKSPACE/docker_build_and_install/docker.cid > $WORKSPACE/docker_build_and_install/subprocess_reaper.log 2>&1 &',
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - build and install"',
        '# build and run build_and_install Dockerfile',
        'cd $WORKSPACE/docker_build_and_install',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build --force-rm -t devel_build_and_install.%s_%s .' % (rosdistro_name, source_repo_spec.name.lower()),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - build and install"',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_build_and_install/docker.cid' +
        ' -e=TRAVIS=$TRAVIS' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/catkin_workspace:/tmp/catkin_workspace' +
        ' devel_build_and_install.%s_%s' % (rosdistro_name, source_repo_spec.name.lower()),
        'cd -',  # restore pwd when used in scripts
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ --cid-file $WORKSPACE/docker_build_and_test/docker.cid > $WORKSPACE/docker_build_and_test/subprocess_reaper.log 2>&1 &',
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - build and test"',
        '# build and run build_and_test Dockerfile',
        'cd $WORKSPACE/docker_build_and_test',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build --force-rm -t devel_build_and_test.%s_%s .' % (rosdistro_name, source_repo_spec.name.lower()),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - build and test"',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_build_and_test/docker.cid' +
        ' -e=TRAVIS=$TRAVIS' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/catkin_workspace:/tmp/catkin_workspace' +
        ' devel_build_and_test.%s_%s' % (rosdistro_name, source_repo_spec.name.lower()),
        'cd -',  # restore pwd when used in scripts
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'if [ "$skip_cleanup" = "false" ]; then',
        'echo "# BEGIN SECTION: Clean up to save disk space on agents"',
        'rm -fr catkin_workspace/build_isolated',
        'rm -fr catkin_workspace/devel_isolated',
        'rm -fr catkin_workspace/install_isolated',
        'echo "# END SECTION"',
        'fi',
    ]),
))@
  </builders>
  <publishers>
@(SNIPPET(
    'publisher_warnings',
    unstable_threshold=0 if notify_compiler_warnings else '',
))@
@(SNIPPET(
    'publisher_xunit',
    pattern='catkin_workspace/test_results/**/*.xml',
))@
@[if not pull_request or notify_pull_requests]@
@[ if notify_maintainers]@
@(SNIPPET(
    'publisher_groovy-postbuild_maintainer-notification',
))@
@[ end if]@
@(SNIPPET(
    'publisher_mailer',
    recipients=notify_emails,
    dynamic_recipients=maintainer_emails,
    send_to_individuals=notify_committers,
))@
@[end if]@
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
@[if git_ssh_credential_id]@
@(SNIPPET(
    'build-wrapper_ssh-agent',
    credential_ids=[git_ssh_credential_id],
))@
@[end if]@
  </buildWrappers>
</project>
