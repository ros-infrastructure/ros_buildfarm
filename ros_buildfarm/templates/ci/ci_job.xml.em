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
    'property_authorization-matrix',
    project_authorization_xml=project_authorization_xml,
))@
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
        'description': 'Skip cleanup of build artifacts as well as rosdoc index',
    },
    {
        'type': 'string',
        'name': 'install_packages',
        'default_value': ' '.join(install_packages),
        'description': 'Package(s) to be installed prior to any packages detected for installation by rosdep (space-separated)',
    },
    {
        'type': 'string',
        'name': 'repos_file_urls',
        'default_value': ' '.join(repos_file_urls),
        'description': 'URL(s) of repos file(s) containing the list of packages to be built (space-separated)',
    },
    {
        'type': 'string',
        'name': 'repository_names',
        'default_value': ' '.join(repository_names),
        'description': 'Repositories names from the rosdistro to be built (space-separated)',
    },
    {
        'type': 'string',
        'name': 'test_branch',
        'default_value': test_branch or '',
        'description': 'Branch to attempt to checkout before doing batch job',
    },
    {
        'type': 'string',
        'name': 'package_selection_args',
        'default_value': package_selection_args or '',
        'description': 'Package selection arguments passed to colcon to specify which packages should be built and tested, or blank for ALL',
    },
    {
        'type': 'string',
        'name': 'build_tool_args',
        'default_value': build_tool_args or '',
        'description': 'Arbitrary arguments passed to the build tool',
    },
    {
        'type': 'string',
        'name': 'build_tool_test_args',
        'default_value': build_tool_test_args or '',
        'description': 'Arbitrary arguments passed to the build tool during testing',
    },
]
}@
@(SNIPPET(
    'property_parameters-definition',
    parameters=parameters,
))@
@(SNIPPET(
    'property_job-weight',
    weight=job_weight,
))@
  </properties>
  <scm class="hudson.scm.NullSCM"/>
  <scmCheckoutRetryCount>2</scmCheckoutRetryCount>
  <assignedNode>@(node_label)</assignedNode>
  <canRoam>false</canRoam>
  <disabled>@('true' if disabled else 'false')</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers>
@[if trigger_jobs]@
@(SNIPPET(
    'trigger_reverse-build',
    upstream_projects=trigger_jobs,
))@
@[end if]@
@[if trigger_timer is not None]@
@(SNIPPET(
    'trigger_timer',
    spec=trigger_timer,
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
@[if underlay_source_jobs]@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Prepare package underlay"',
    ]),
))@
@[for i, underlay_source_job in enumerate(underlay_source_jobs, 1)]@
@(SNIPPET(
    'copy_artifacts',
    artifacts=[
      '*.tar.bz2',
    ],
    project=underlay_source_job,
    target_directory='$WORKSPACE/underlay%d' % (i),
))@
@[end for]@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'tar -xjf $WORKSPACE/underlay%d/*.tar.bz2 -C $WORKSPACE/underlay%d' %
        (i + 1, i + 1) for i in range(len(underlay_source_jobs))
    ] + [
        'echo "# END SECTION"',
    ]),
))@
@[end if]@
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
        '# create a unique dockerfile name prefix',
        '[ -z "$EXECUTOR_NUMBER" ] && export EXECUTOR_NUMBER=0',
        'export DOCKER_IMAGE_PREFIX=executor_$EXECUTOR_NUMBER',
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
        ' --build-tool ' + build_tool +
        ' --ros-version ' + str(ros_version) +
        ' --env-vars ' + ' '.join([v.replace('$', '\\$',) for v in build_environment_variables]) +
        ' --dockerfile-dir $WORKSPACE/docker_generating_dockers' +
        ' --repos-file-urls $repos_file_urls' +
        ' --repository-names $repository_names' +
        ' --test-branch "$test_branch"' +
        ' --skip-rosdep-keys ' + ' '.join(skip_rosdep_keys) +
        ' --install-packages $install_packages' +
        ' --workspace-mount-point /tmp/ws' + ''.join([
            ' /tmp/ws%d' % (i + 2) for i in range(len(underlay_source_paths))
        ]) +
        ' --package-selection-args $package_selection_args' +
        ' --build-tool-args $build_tool_args' +
        ' --build-tool-test-args $build_tool_test_args',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - generating CI tasks"',
        'cd $WORKSPACE/docker_generating_dockers',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build --force-rm -t $DOCKER_IMAGE_PREFIX.ci_task_generation.%s .' % (rosdistro_name),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - generating CI tasks"',
        'rm -fr $WORKSPACE/docker_create_workspace',
        'rm -fr $WORKSPACE/docker_build_and_install',
        'rm -fr $WORKSPACE/docker_build_and_test',
        'mkdir -p $WORKSPACE/docker_create_workspace',
        'mkdir -p $WORKSPACE/docker_build_and_install',
        'mkdir -p $WORKSPACE/docker_build_and_test',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_generating_dockers/docker.cid' +
        ' -e=HOME=/home/buildfarm' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/docker_create_workspace:/tmp/docker_create_workspace' +
        ' -v $WORKSPACE/docker_build_and_install:/tmp/docker_build_and_install' +
        ' -v $WORKSPACE/docker_build_and_test:/tmp/docker_build_and_test' +
        ' $DOCKER_IMAGE_PREFIX.ci_task_generation.%s' % (rosdistro_name),
        'cd -',  # restore pwd when used in scripts
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ --cid-file $WORKSPACE/docker_create_workspace/docker.cid > $WORKSPACE/docker_create_workspace/subprocess_reaper.log 2>&1 &',
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        '# create a unique dockerfile name prefix',
        'export DOCKER_IMAGE_PREFIX=$(date +%s.%N)',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - create workspace"',
        '# build and run create_workspace Dockerfile',
        'cd $WORKSPACE/docker_create_workspace',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build --force-rm -t $DOCKER_IMAGE_PREFIX.ci_create_workspace.%s .' % (rosdistro_name),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - create workspace"',
    ] + [
        'export UNDERLAY%d_JOB_SPACE=$WORKSPACE/underlay%d/ros%d-linux' % (i + 1, i + 1, local_ros_version)
        for i, local_ros_version in zip(range(len(underlay_source_jobs)), [ros_version] * len(underlay_source_jobs))
    ] + [
        'rm -fr $WORKSPACE/ws/src',
        'mkdir -p $WORKSPACE/ws/src',
    ] + [
        'mkdir -p %s' % (dir) for dir in underlay_source_paths
    ] + [
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_create_workspace/docker.cid' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ''.join([
            ' -v %s:/tmp/ws%s/install_isolated:ro' % (space, i if i > 1 else '')
            for i, space in enumerate(underlay_source_paths, 1)
        ]) +
        ' -v $WORKSPACE/ws:/tmp/ws%s' % (len(underlay_source_paths) + 1 if len(underlay_source_paths) else '') +
        ' $DOCKER_IMAGE_PREFIX.ci_create_workspace.%s' % (rosdistro_name),
        'cd -',  # restore pwd when used in scripts
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Copy dependency list"',
        '/bin/cp -f $WORKSPACE/ws/install_list_build.txt $WORKSPACE/docker_build_and_install/install_list_build.txt',
        '/bin/cp -f $WORKSPACE/ws/install_list_build.txt $WORKSPACE/docker_build_and_test/install_list_build.txt',
        '/bin/cp -f $WORKSPACE/ws/install_list_test.txt $WORKSPACE/docker_build_and_test/install_list_test.txt',
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
        '# create a unique dockerfile name prefix',
        'export DOCKER_IMAGE_PREFIX=$(date +%s.%N)',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - build and install"',
        '# build and run build and install Dockerfile',
        'cd $WORKSPACE/docker_build_and_install',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build --force-rm -t $DOCKER_IMAGE_PREFIX.ci_build_and_install.%s .' % (rosdistro_name),
        'echo "# END SECTION"',
        '',
    ] + ([
        'echo "# BEGIN SECTION: ccache stats (before)"',
        'mkdir -p $HOME/.ccache',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_build_and_install/docker_ccache_before.cid' +
        ' -e CCACHE_DIR=/home/buildfarm/.ccache' +
        ' -v $HOME/.ccache:/home/buildfarm/.ccache' +
        ' $DOCKER_IMAGE_PREFIX.ci_build_and_install.%s' % (rosdistro_name) +
        ' "ccache -s"',
        'echo "# END SECTION"',
        '',
    ] if shared_ccache else []) + [
        'echo "# BEGIN SECTION: Run Dockerfile - build and install"',
    ] + [
        'export UNDERLAY%d_JOB_SPACE=$WORKSPACE/underlay%d/ros%d-linux' % (i + 1, i + 1, local_ros_version)
        for i, local_ros_version in zip(range(len(underlay_source_jobs)), [ros_version] * len(underlay_source_jobs))
    ] + [
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_build_and_install/docker.cid' +
        ((' -e CCACHE_DIR=/home/buildfarm/.ccache' +
          ' -v $HOME/.ccache:/home/buildfarm/.ccache') if shared_ccache else '') +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ''.join([
            ' -v %s:/tmp/ws%s/install_isolated:ro' % (space, i if i > 1 else '')
            for i, space in enumerate(underlay_source_paths, 1)
        ]) +
        ' -v $WORKSPACE/ws:/tmp/ws%s' % (len(underlay_source_paths) + 1 if len(underlay_source_paths) else '') +
        ' $DOCKER_IMAGE_PREFIX.ci_build_and_install.%s' % (rosdistro_name),
        'cd -',  # restore pwd when used in scripts
        'echo "# END SECTION"',
    ] + ([
        '',
        'echo "# BEGIN SECTION: ccache stats (after)"',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_build_and_install/docker_ccache_after.cid' +
        ' -e CCACHE_DIR=/home/buildfarm/.ccache' +
        ' -v $HOME/.ccache:/home/buildfarm/.ccache' +
        ' $DOCKER_IMAGE_PREFIX.ci_build_and_install.%s' % (rosdistro_name) +
        ' "ccache -s"',
        'echo "# END SECTION"',
    ] if shared_ccache else [])),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Compress install space"',
        'tar -cjf $WORKSPACE/ros%d-%s-linux-%s-%s-ci.tar.bz2 ' % (ros_version, rosdistro_name, os_code_name, arch) +
        ' -C $WORKSPACE/ws' +
        ' --transform "s/^install_isolated/ros%d-linux/"' % (ros_version) +
        ' install_isolated',
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
        '# create a unique dockerfile name prefix',
        'export DOCKER_IMAGE_PREFIX=$(date +%s.%N)',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - build and test"',
        '# build and run build and test Dockerfile',
        'cd $WORKSPACE/docker_build_and_test',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build --force-rm -t $DOCKER_IMAGE_PREFIX.ci_build_and_test.%s .' % (rosdistro_name),
        'echo "# END SECTION"',
        '',
    ] + ([
        'echo "# BEGIN SECTION: ccache stats (before)"',
        'mkdir -p $HOME/.ccache',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_build_and_test/docker_ccache_before.cid' +
        ' -e CCACHE_DIR=/home/buildfarm/.ccache' +
        ' -v $HOME/.ccache:/home/buildfarm/.ccache' +
        ' $DOCKER_IMAGE_PREFIX.ci_build_and_test.%s' % (rosdistro_name) +
        ' "ccache -s"',
        'echo "# END SECTION"',
        '',
    ] if shared_ccache else []) + [
        'echo "# BEGIN SECTION: Run Dockerfile - build and test"',
    ] + [
        'export UNDERLAY%d_JOB_SPACE=$WORKSPACE/underlay%d/ros%d-linux' % (i + 1, i + 1, local_ros_version)
        for i, local_ros_version in zip(range(len(underlay_source_jobs)), [ros_version] * len(underlay_source_jobs))
    ] + [
        'rm -fr $WORKSPACE/ws/test_results',
        'mkdir -p $WORKSPACE/ws/test_results',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_build_and_test/docker.cid' +
        ((' -e CCACHE_DIR=/home/buildfarm/.ccache' +
          ' -v $HOME/.ccache:/home/buildfarm/.ccache') if shared_ccache else '') +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ''.join([
            ' -v %s:/tmp/ws%s/install_isolated:ro' % (space, i if i > 1 else '')
            for i, space in enumerate(underlay_source_paths, 1)
        ]) +
        ' -v $WORKSPACE/ws:/tmp/ws%s' % (len(underlay_source_paths) + 1 if len(underlay_source_paths) else '') +
        ' $DOCKER_IMAGE_PREFIX.ci_build_and_test.%s' % (rosdistro_name),
        'cd -',  # restore pwd when used in scripts
        'echo "# END SECTION"',
    ] + ([
        '',
        'echo "# BEGIN SECTION: ccache stats (after)"',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_build_and_test/docker_ccache_after.cid' +
        ' -e CCACHE_DIR=/home/buildfarm/.ccache' +
        ' -v $HOME/.ccache:/home/buildfarm/.ccache' +
        ' $DOCKER_IMAGE_PREFIX.ci_build_and_test.%s' % (rosdistro_name) +
        ' "ccache -s"',
        'echo "# END SECTION"',
    ] if shared_ccache else [])),
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
  </builders>
  <publishers>
@(SNIPPET(
    'publisher_warnings',
    build_tool=build_tool,
    unstable_threshold='',
))@
@(SNIPPET(
    'archive_artifacts',
    artifacts=[
      'ros%d-%s-linux-%s-%s-ci.tar.bz2' % (ros_version, rosdistro_name, os_code_name, arch),
    ] + archive_files + [
      image for images in show_images.values() for image in images
    ],
))@
@[if benchmark_patterns]@
@(SNIPPET(
    'publisher_benchmark',
    patterns=benchmark_patterns,
    schema=benchmark_schema,
))@
@[end if]@
@[for title, artifacts in show_images.items()]@
@(SNIPPET(
    'image_gallery',
    title=title,
    image_width='',
    artifacts=artifacts,
))@
@[end for]@
@[if show_plots]@
@(SNIPPET(
    'plot_plugin',
    plots=show_plots,
))@
@[end if]@
@[if xunit_publisher_types]@
@(SNIPPET(
    'publisher_xunit',
    types=xunit_publisher_types,
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
  </buildWrappers>
</project>
