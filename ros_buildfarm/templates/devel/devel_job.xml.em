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
    'property_rebuild-settings',
))@
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
@(SNIPPET(
    'property_job-weight',
))@
  </properties>
@[if not pull_request]@
@(SNIPPET(
    'scm',
    repo_spec=source_repo_spec,
    path='ws/src/%s' % source_repo_spec.name,
    git_ssh_credential_id=git_ssh_credential_id,
))@
@[else]@
@(SNIPPET(
    'scm_git',
    url=source_repo_spec.url,
    refspec='+refs/pull/*:refs/remotes/origin/pr/*',
    branch_name='${sha1}',
    relative_target_dir='ws/src/%s' % source_repo_spec.name,
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
        '# define the build tool arguments',
        'export build_tool_args="' + (build_tool_args or '').replace('\\', '\\\\') + '"',
        'export build_tool_test_args="' + (build_tool_test_args or '').replace('\\', '\\\\') + '"',
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
        ' --build-tool ' + build_tool +
        ' --ros-version ' + str(ros_version) +
        (' --run-abichecker' if run_abichecker else '') +
        (' --require-gpu-support' if require_gpu_support else '') +
        ' --env-vars ' + ' '.join(build_environment_variables) +
        ' --dockerfile-dir $WORKSPACE/docker_generating_dockers' +
        ' --build-tool-args $build_tool_args' +
        ' --build-tool-test-args $build_tool_test_args',
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
        ' -v $WORKSPACE/ws:/tmp/ws:ro' +
        ' -v $WORKSPACE/docker_build_and_install:/tmp/docker_build_and_install' +
        ' -v $WORKSPACE/docker_build_and_test:/tmp/docker_build_and_test' +
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
    ] + ([
        'if [ ! -d "$HOME/.ccache" ]; then mkdir $HOME/.ccache; fi',
    ]  if shared_ccache else []) + [
        ('if [ ! -c /dev/nvidia[0-9] ]; then echo "--require-gpu-support is enabled but can not detect nvidia support installed" && exit 1; fi' if require_gpu_support else ''),
        'docker run' +
        (' --env=DISPLAY=:0.0 --env=QT_X11_NO_MITSHM=1 --volume=/tmp/.X11-unix:/tmp/.X11-unix:rw --gpus all' if require_gpu_support else '') +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_build_and_install/docker.cid' +
        ' -e=TRAVIS=$TRAVIS' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/ws:/tmp/ws' +
        (' -v $HOME/.ccache:/home/buildfarm/.ccache' if shared_ccache else '') +
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
        '',
    ] + ([
        'if [ ! -d "$HOME/.ccache" ]; then mkdir $HOME/.ccache; fi',
    ] if shared_ccache else []) + [
        'docker run' +
        (' --env=DISPLAY=:0.0 --env=QT_X11_NO_MITSHM=1 --volume=/tmp/.X11-unix:/tmp/.X11-unix:rw  --gpus all' if require_gpu_support else '') +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_build_and_test/docker.cid' +
        ' -e=TRAVIS=$TRAVIS' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/ws:/tmp/ws' +
        (' -v $HOME/.ccache:/home/buildfarm/.ccache' if shared_ccache else '') +
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
        'rm -fr ws/build_isolated',
        'rm -fr ws/devel_isolated',
        'rm -fr ws/install_isolated',
        'echo "# END SECTION"',
        'fi',
    ]),
))@
@[if (not pull_request) and collate_test_stats]@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Create collated test stats dir"',
        'rm -fr $WORKSPACE/collated_test_stats',
        'mkdir -p $WORKSPACE/collated_test_stats',
        'echo "# END SECTION"',
    ]),
))@
@[end if]@
  </builders>
  <publishers>
@(SNIPPET(
    'publisher_warnings',
    build_tool=build_tool,
    unstable_threshold=1 if notify_compiler_warnings else '',
))@
@[if benchmark_patterns]@
@(SNIPPET(
    'publisher_benchmark',
    patterns=benchmark_patterns,
    schema=benchmark_schema,
))@
@[end if]@
@[if xunit_publisher_types]@
@(SNIPPET(
    'publisher_xunit',
    types=xunit_publisher_types,
))@
@[end if]@
@[if (not pull_request) and collate_test_stats]@
@(SNIPPET(
    'publisher_groovy-postbuild',
    script='\n'.join([
        '// COLLATE BUILD TEST RESULTS AND EXPORT BUILD HISTORY FOR WIKI',
        'import jenkins.model.Jenkins',
        'import hudson.FilePath',
        '',
        'import org.jenkinsci.plugins.pipeline.utility.steps.shaded.org.yaml.snakeyaml.Yaml',
        'import org.jenkinsci.plugins.pipeline.utility.steps.shaded.org.yaml.snakeyaml.DumperOptions',
        '',
        'manager.listener.logger.println("# BEGIN SECTION: Collate test results for wiki.")',
        '',
        '// nr of builds to include in history',
        'final num_build_hist = 5',
        '',
        'try {',
        '  def data = [',
        '    "history" : []',
        '  ]',
        '',
        '  // gather info on tests of current build',
        '  def tresult = manager.build.getAction(hudson.tasks.junit.TestResultAction.class)?.result',
        '  if (tresult) {',
        '    data.latest_build = [',
        '      "skipped" : tresult.skipCount,',
        '      "failed" : tresult.failCount,',
        '      "total" : tresult.totalCount',
        '    ]',
        '  }',
        '  else {',
        '    manager.listener.logger.println("No test result action for last build, skipping gathering statistics for it.")',
        '  }',
        '',
        '',
        '  // get access to the job of the running build',
        '  def job_name = manager.build.getEnvironment(manager.listener).get(\'JOB_NAME\')',
        '  manager.listener.logger.println("Collating test statistics for \'${job_name}\'.")',
        '  def job = Jenkins.instance.getItem(job_name)',
        '  if (job == null) {',
        '    manager.listener.logger.println("No such job: \'${job_name}\'.")',
        '    return',
        '  }',
        '',
        '  // store base info',
        '  data.base_url = Jenkins.instance.getRootUrl()',
        '  data.total_builds = job.builds.size()',
        '  data.job_health = job.getBuildHealth().getScore()',
        '  data.job_health_icon = job.getBuildHealth().getIconClassName()',
        '',
        '  // retrieve info on last N builds of this job',
        '  job.builds.take(num_build_hist).each { b ->',
        '    tresult = b.getAction(hudson.tasks.junit.TestResultAction.class)?.result',
        '    if (tresult) {',
        '      data.history << [',
        '        "build_id" : b.id as Integer,',
        '        "uri" : b.url,',
        '        "stamp" : b.getStartTimeInMillis() / 1e3,',
        '        "result" :  b.result.toString().toLowerCase(),',
        '        "tests" : [',
        '          "skipped" : tresult.skipCount,',
        '          "failed" : tresult.failCount,',
        '          "total" : tresult.totalCount',
        '        ]',
        '      ]',
        '    }',
        '  }',
        '',
        '  // write out info to file',
        '  def DumperOptions options = new DumperOptions()',
        '  options.setPrettyFlow(true)',
        '  options.setDefaultFlowStyle(DumperOptions.FlowStyle.BLOCK)',
        '  def yaml_output = new Yaml(options).dump([\'dev_job_data\' : data])',
        '',
        '  def fp = new FilePath(manager.build.workspace, "collated_test_stats/results.yaml")',
        '  if(fp != null)',
        '    fp.write(yaml_output, null)',
        '  else',
        '    manager.listener.logger.println("Could not write to yaml file (fp == null)")',
        '',
        '} finally {',
        '  manager.listener.logger.println("# END SECTION")',
        '}',
    ]),
))
@(SNIPPET(
    'publisher_publish-over-ssh',
    config_name='docs',
    remote_directory='%s/devel_jobs/%s' % (rosdistro_name, source_repo_spec.name),
    source_files=[
        'collated_test_stats/results.yaml'
    ],
    remove_prefix='collated_test_stats',
))@
@[end if]@
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
@[if run_abichecker]
@(SNIPPET(
    'publisher_abi_report',
))@
@(SNIPPET(
    'publisher_parser_unstable',
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
