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
        'description': 'Skip cleanup of colcon build artifacts as well as rosdoc index',
    },
]
}@
@(SNIPPET(
    'property_parameters-definition',
    parameters=parameters,
))@
  </properties>
  <scmCheckoutRetryCount>2</scmCheckoutRetryCount>
  <assignedNode>@(node_label)</assignedNode>
  <canRoam>false</canRoam>
  <disabled>@('true' if disabled else 'false')</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers>
@(SNIPPET(
    'trigger_timer',
    spec='0 23 * * *',
))@
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
        '# generating the Dockerfiles for the actual CI tasks',
        'echo "# BEGIN SECTION: Generate Dockerfile - CI tasks"',
        'export TZ="%s"' % timezone,
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/ci/run_ci_job.py' +
        ' ' + rosdistro_name +
        ' ' + os_name +
        ' ' + os_code_name +
        ' ' + arch +
        ' ' + ' '.join(repository_args) +
        ' --repos-file-urls ' + ' '.join(repos_files) +
        ' --dockerfile-dir $WORKSPACE/docker_generating_dockers' +
        ' --skip-rosdep-keys ' + ' '.join(skip_rosdep_keys),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - generating CI tasks"',
        'cd $WORKSPACE/docker_generating_dockers',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build --force-rm -t ci_task_generation.%s .' % (rosdistro_name),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - generating CI tasks"',
        'rm -fr $WORKSPACE/docker_create_workspace',
        'rm -fr $WORKSPACE/docker_colcon_build',
        'mkdir -p $WORKSPACE/docker_create_workspace',
        'mkdir -p $WORKSPACE/docker_colcon_build',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_generating_dockers/docker.cid' +
        ' -e=HOME=/home/buildfarm' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/docker_create_workspace:/tmp/docker_create_workspace' +
        ' -v $WORKSPACE/docker_colcon_build:/tmp/docker_colcon_build' +
        ' ci_task_generation.%s' % (rosdistro_name),
        'cd -',  # restore pwd when used in scripts
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ --cid-file $WORKSPACE/docker_colcon_build/docker.cid > $WORKSPACE/docker_colcon_build/subprocess_reaper.log 2>&1 &',
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - create workspace"',
        '# build and run create_workspace Dockerfile',
        'cd $WORKSPACE/docker_create_workspace',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build --force-rm -t ci_create_workspace.%s .' % (rosdistro_name),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - create workspace"',
        'rm -fr $WORKSPACE/colcon_workspace/src',
        'mkdir -p $WORKSPACE/colcon_workspace/src',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_create_workspace/docker.cid' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/colcon_workspace:/tmp/colcon_workspace' +
        ' ci_create_workspace.%s' % (rosdistro_name),
        'cd -',  # restore pwd when used in scripts
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Copy dependency list"',
        '/bin/cp -f $WORKSPACE/colcon_workspace/install_list.txt $WORKSPACE/docker_colcon_build/',
        'echo "# END SECTION"',
        'echo "# BEGIN SECTION: Ignore some packages"',
    ] +
    [
        'touch $WORKSPACE/colcon_workspace/src/ros2/%s/COLCON_IGNORE' % (subdir) for subdir in build_ignore
    ] +
    [
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ --cid-file $WORKSPACE/docker_colcon_build/docker.cid > $WORKSPACE/docker_colcon_build/subprocess_reaper.log 2>&1 &',
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - colcon build"',
        '# build and run colcon_build Dockerfile',
        'cd $WORKSPACE/docker_colcon_build',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build --force-rm -t ci_colcon_build.%s .' % (rosdistro_name),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: ccache stats (before)"',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_colcon_build/docker_ccache_before.cid' +
        ' -e CCACHE_DIR=/home/buildfarm/.ccache' +
        ' -v $HOME/.ccache:/home/buildfarm/.ccache' +
        ' ci_colcon_build.%s' % (rosdistro_name) +
        ' "ccache -s"',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - colcon build"',
        'rm -fr $WORKSPACE/colcon_workspace/test_results',
        'mkdir -p $WORKSPACE/colcon_workspace/test_results',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_colcon_build/docker.cid' +
        ' -e CCACHE_DIR=/home/buildfarm/.ccache' +
        ' -v $HOME/.ccache:/home/buildfarm/.ccache' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/colcon_workspace:/tmp/colcon_workspace' +
        ' ci_colcon_build.%s' % (rosdistro_name),
        'cd -',  # restore pwd when used in scripts
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: ccache stats (after)"',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_colcon_build/docker_ccache_after.cid' +
        ' -e CCACHE_DIR=/home/buildfarm/.ccache' +
        ' -v $HOME/.ccache:/home/buildfarm/.ccache' +
        ' ci_colcon_build.%s' % (rosdistro_name) +
        ' "ccache -s"',
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Compress install space"',
        'tar -cjf $WORKSPACE/ros2-%s-linux-%s-%s-ci.tar.bz2 -C $WORKSPACE/colcon_workspace --transform "s/^install_merged/ros2-linux/" install_merged' % (rosdistro_name, os_code_name, arch),
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'if [ "$skip_cleanup" = "false" ]; then',
        'echo "# BEGIN SECTION: Clean up to save disk space on agents"',
        'rm -fr colcon_workspace/build',
        'rm -fr colcon_workspace/install_merged',
        'echo "# END SECTION"',
        'fi',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Create collated test stats dir"',
        'rm -fr $WORKSPACE/collated_test_stats',
        'mkdir -p $WORKSPACE/collated_test_stats',
        'echo "# END SECTION"',
    ]),
))@
  </builders>
  <publishers>
@(SNIPPET(
    'publisher_warnings',
    unstable_threshold='',
))@
@(SNIPPET(
    'archive_artifacts',
    artifacts=[
      'ros2-%s-linux-%s-%s-ci.tar.bz2' % (rosdistro_name, os_code_name, arch),
    ],
))@
@(SNIPPET(
    'publisher_xunit',
    pattern='colcon_workspace/test_results/**/*.xml',
))@
@(SNIPPET(
    'publisher_groovy-postbuild',
    script='\n'.join([
        '// COLLATE BUILD TEST RESULTS AND EXPORT BUILD HISTORY FOR WIKI',
        'import jenkins.model.Jenkins',
        'import hudson.FilePath',
        '',
        '@Grab(\'org.yaml:snakeyaml:1.17\')',
        'import org.yaml.snakeyaml.Yaml',
        'import org.yaml.snakeyaml.DumperOptions',
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
    remote_directory='%s/devel_jobs' % (rosdistro_name),
    source_files=[
        'collated_test_stats/results.yaml'
    ],
    remove_prefix='collated_test_stats',
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
