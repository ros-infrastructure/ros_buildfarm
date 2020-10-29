<project>
  <actions/>
  <description>Generated at @ESCAPE(now_str) from template '@ESCAPE(template_name)'</description>
  <keepDependencies>false</keepDependencies>
  <properties>
@(SNIPPET(
    'property_log-rotator',
    days_to_keep=100,
    num_to_keep=100,
))@
@(SNIPPET(
    'property_job-priority',
    priority=-1,
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
  <assignedNode>building_repository</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>true</blockBuildWhenUpstreamBuilding>
  <triggers/>
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
        'rm -fr $WORKSPACE/docker_check_sync_criteria',
        'mkdir -p $WORKSPACE/docker_check_sync_criteria',
        '',
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ --cid-file $WORKSPACE/docker_check_sync_criteria/docker.cid > $WORKSPACE/docker_check_sync_criteria/subprocess_reaper.log 2>&1 &',
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        '# generate Dockerfile, build and run it',
        '# checking the sync criteria',
        'echo "# BEGIN SECTION: Generate Dockerfile - check sync condition"',
        'export TZ="%s"' % timezone,
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/release/run_check_sync_criteria_job.py' +
        ' ' + config_url +
        ' ' + rosdistro_name +
        ' ' + release_build_name +
        ' ' + os_name +
        ' ' + os_code_name +
        ' ' + arch +
        ' ' + ' '.join(repository_args) +
        ' --cache-dir /tmp/package_repo_cache' +
        ' --dockerfile-dir $WORKSPACE/docker_check_sync_criteria',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - check sync condition"',
        'cd $WORKSPACE/docker_check_sync_criteria',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build --force-rm -t check_sync_condition .',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - check sync condition"',
        'rm -fr $WORKSPACE/package_repo_cache',
        'mkdir -p $WORKSPACE/package_repo_cache',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_check_sync_criteria/docker.cid' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/package_repo_cache:/tmp/package_repo_cache' +
        ' check_sync_condition',
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Clone custom reprepro-updater"',
        'rm -fr reprepro-updater',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/wrapper/git.py clone --depth 1 -b refactor https://github.com/ros-infrastructure/reprepro-updater.git reprepro-updater',
        'git -C reprepro-updater log -n 1',
        'rm -fr reprepro-updater/.git',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: sync source packages to testing repo"',
        'export PYTHONPATH=$WORKSPACE/reprepro-updater/src:$PYTHONPATH',
        'python3 -u $WORKSPACE/reprepro-updater/scripts/sync_ros_packages.py ubuntu_testing --upstream-ros ubuntu_building -r %s -d %s -a source -c' % (rosdistro_name, os_code_name),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: sync binary packages to testing repo"',
        'export PYTHONPATH=$WORKSPACE/reprepro-updater/src:$PYTHONPATH',
        'python3 -u $WORKSPACE/reprepro-updater/scripts/sync_ros_packages.py ubuntu_testing --upstream-ros ubuntu_building -r %s -d %s -a %s -c' % (rosdistro_name, os_code_name, arch),
        'echo "# END SECTION"',
    ]),
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
@(SNIPPET(
    'build-wrapper_timestamper',
))@
  </buildWrappers>
</project>
