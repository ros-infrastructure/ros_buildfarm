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
@[if pull_request]@
@(SNIPPET(
    'property_parameters-definition',
    parameters=[
        {
            'type': 'string',
            'name': 'sha1',
        },
    ],
))@
@[end if]@
@(SNIPPET(
    'property_requeue-job',
))@
@(SNIPPET(
    'property_disk-usage',
))@
  </properties>
@[if not pull_request]@
@(SNIPPET(
    'scm',
    repo_spec=source_repo_spec,
    path='catkin_workspace/src/%s' % source_repo_spec.name,
))@
@[end if]@
@[if pull_request]@
@(SNIPPET(
    'scm_git',
    url=source_repo_spec.url,
    refspec='+refs/pull/*:refs/remotes/origin/pr/*',
    branch_name='${sha1}',
    relative_target_dir='catkin_workspace/src/%s' % source_repo_spec.name,
))@
@[end if]@
  <assignedNode>buildslave</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
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
    'builder_shell_docker-info',
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Clone ros_buildfarm"',
        'rm -fr ros_buildfarm',
        'git clone %s ros_buildfarm' % ros_buildfarm_url,
        'echo "# END SECTION"',
    ]),
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
        'echo "# BEGIN SECTION: Generate Dockerfile - devel tasks"',
        'export TZ="%s"' % timezone,
        'mkdir -p $WORKSPACE/docker_generating_dockers',
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
        'docker build -t devel_task_generation__%s_%s .' % (rosdistro_name, source_repo_spec.name),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - generating devel tasks"',
        'mkdir -p $WORKSPACE/docker_build_and_install',
        'mkdir -p $WORKSPACE/docker_build_and_test',
        'docker run' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/catkin_workspace:/tmp/catkin_workspace:ro' +
        ' -v $WORKSPACE/docker_build_and_install:/tmp/docker_build_and_install' +
        ' -v $WORKSPACE/docker_build_and_test:/tmp/docker_build_and_test' +
        ' devel_task_generation__%s_%s' % (rosdistro_name, source_repo_spec.name),
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Build Dockerfile - build and install"',
        '# build and run build_and_install Dockerfile',
        'cd $WORKSPACE/docker_build_and_install',
        'docker build -t devel_build_and_install__%s_%s .' % (rosdistro_name, source_repo_spec.name),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - build and install"',
        'docker run' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/catkin_workspace:/tmp/catkin_workspace' +
        ' devel_build_and_install__%s_%s' % (rosdistro_name, source_repo_spec.name),
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Build Dockerfile - build and test"',
        '# build and run build_and_test Dockerfile',
        'cd $WORKSPACE/docker_build_and_test',
        'docker build -t devel_build_and_test__%s_%s .' % (rosdistro_name, source_repo_spec.name),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - build and test"',
        'docker run' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/catkin_workspace:/tmp/catkin_workspace' +
        ' devel_build_and_test__%s_%s' % (rosdistro_name, source_repo_spec.name),
        'echo "# END SECTION"',
    ]),
))@
  </builders>
  <publishers>
@(SNIPPET(
    'publisher_xunit',
    pattern='catkin_workspace/test_results/**/*.xml',
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
    send_to_individuals=notify_committers,
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
@(SNIPPET(
    'build-wrapper_disk-check',
))@
  </buildWrappers>
</project>
