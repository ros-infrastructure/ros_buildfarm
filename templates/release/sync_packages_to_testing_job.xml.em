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
@(SNIPPET(
    'property_requeue-job',
))@
  </properties>
@(SNIPPET(
    'scm_git',
    url=ros_buildfarm_url,
    refspec='master',
    relative_target_dir='ros_buildfarm',
))@
  <assignedNode>building_repository</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
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
        '# checking the sync criteria',
        'echo "# BEGIN SECTION: Generate Dockerfile - check sync condition"',
        'mkdir -p $WORKSPACE/docker_check_sync_criteria',
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        '$WORKSPACE/ros_buildfarm/scripts/release/run_check_sync_criteria_job.py' +
        ' ' + config_url +
        ' ' + rosdistro_name +
        ' ' + release_build_name +
        ' ' + os_code_name +
        ' ' + arch +
        ' ' + ' '.join(repository_args) +
        ' --cache-dir /tmp/debian_repo_cache' +
        ' --dockerfile-dir $WORKSPACE/docker_check_sync_criteria',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - check sync condition"',
        'cd $WORKSPACE/docker_check_sync_criteria',
        'docker build -t check_sync_condition .',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - check sync condition"',
        'rm -fr $WORKSPACE/debian_repo_cache',
        'mkdir -p $WORKSPACE/debian_repo_cache',
        'docker run' +
        ' -v $WORKSPACE/rosdistro:/tmp/rosdistro:ro' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/debian_repo_cache:/tmp/debian_repo_cache' +
        ' check_sync_condition',
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Clone custom reprepro-updater"',
        'rm -fr reprepro-updater',
        'git clone -b refactor https://github.com/ros-infrastructure/reprepro-updater.git reprepro-updater',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: sync packages to testing repo"',
        'export PYTHONPATH=$WORKSPACE/reprepro-updater/src:$PYTHONPATH',
        '$WORKSPACE/reprepro-updater/scripts/sync_ros_packages.py ubuntu_testing --upstream-ros ubuntu_building -r %s -d %s -a %s -c' % (rosdistro_name, os_code_name, arch),
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
