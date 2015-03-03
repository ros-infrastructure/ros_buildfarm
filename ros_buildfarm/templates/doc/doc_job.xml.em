<project>
  <actions/>
  <description>Generated at @ESCAPE(now_str) from template '@ESCAPE(template_name)'
@[if disabled]@
  but disabled since the package is blacklisted (or not whitelisted) in the configuration file@
@[end if]@
@ </description>
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
@(SNIPPET(
    'property_parameters-definition',
    parameters=[
        {
            'type': 'boolean',
            'name': 'force',
            'description': 'Run documentation generation even if neither the source repository nor any of the tools have changes',
        },
        {
            'type': 'boolean',
            'name': 'skip_cleanup',
            'description': 'Skip cleanup of catkin build artifacts as well as rosdoc index',
        },
    ],
))@
@(SNIPPET(
    'property_requeue-job',
))@
  </properties>
@(SNIPPET(
    'scm',
    repo_spec=doc_repo_spec,
    path='catkin_workspace/src/%s' % doc_repo_spec.name,
))@
  <assignedNode>@(node_label if node_label else 'buildslave')</assignedNode>
  <canRoam>false</canRoam>
  <disabled>@('true' if disabled else 'false')</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers>
@(SNIPPET(
    'trigger_poll',
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
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Clone ros_buildfarm"',
        'rm -fr ros_buildfarm',
        'git clone --depth 1 %s%s ros_buildfarm' % ('-b %s ' % ros_buildfarm_repository.version if ros_buildfarm_repository.version else '', ros_buildfarm_repository.url),
        'git -C ros_buildfarm log -n 1',
        'rm -fr ros_buildfarm/.git',
        'rm -fr ros_buildfarm/doc',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Clone rosdoc_lite"',
        'rm -fr rosdoc_lite',
        'git clone --depth 1 https://github.com/ros-infrastructure/rosdoc_lite.git rosdoc_lite',
        'git -C rosdoc_lite log -n 1',
        'rm -fr rosdoc_lite/.git',
        'rm -fr rosdoc_lite/doc',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Clone catkin-sphinx"',
        'rm -fr catkin-sphinx',
        'git clone --depth 1 https://github.com/ros-infrastructure/catkin-sphinx catkin-sphinx',
        'git -C catkin-sphinx log -n 1',
        'rm -fr catkin-sphinx/.git',
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: rsync (most of) the rosdoc_index to slave"',
        'rm -fr rosdoc_index',
        '# must pass if the rosdistro specific folder does not exist yet',
        'rsync -e "ssh -o StrictHostKeyChecking=no"' +
        ' --prune-empty-dirs --quiet --recursive' +
        ' --include="+ */"' +
        ' --include="%s/deps/*"' % rosdistro_name +
        ' --include="%s/hashes/%s"' % (rosdistro_name, doc_repo_spec.name) +
        ' --include="%s/locations/*"' % rosdistro_name +
        ' --include="%s/metapackage_deps/*"' % rosdistro_name +
        ' --include="%s/symbols/*"' % rosdistro_name +
        ' --exclude="- *"' +
        ' jenkins-slave@repo:/var/repos/docs/ $WORKSPACE/rosdoc_index',
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
        'rm -fr $WORKSPACE/docker_generating_docker',
        'rm -fr $WORKSPACE/generated_documentation',
        'mkdir -p $WORKSPACE/docker_generating_docker',
        'mkdir -p $WORKSPACE/generated_documentation',
        '',
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ --cid-file $WORKSPACE/docker_generating_docker/docker.cid > $WORKSPACE/docker_generating_docker/subprocess_reaper.log 2>&1 &',
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        '# generate Dockerfile, build and run it',
        '# generating the Dockerfiles for the actual doc task',
        'echo "# BEGIN SECTION: Generate Dockerfile - doc task"',
        'export TZ="%s"' % timezone,
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        'if [ "$force" = "true" ]; then FORCE_FLAG="--force"; fi',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/doc/run_doc_job.py' +
        ' ' + config_url +
        ' --rosdistro-index-url ' + rosdistro_index_url +
        ' ' + rosdistro_name +
        ' ' + doc_build_name +
        ' ' + doc_repo_spec.name +
        ' ' + os_name +
        ' ' + os_code_name +
        ' ' + arch +
        ' --vcs-info "%s %s %s"' % (doc_repo_spec.type, doc_repo_spec.version if doc_repo_spec.version is not None else '', doc_repo_spec.url) +
        ' ' + ' '.join(repository_args) +
        ' $FORCE_FLAG' +
        ' --dockerfile-dir $WORKSPACE/docker_generating_docker',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - generating doc task"',
        'cd $WORKSPACE/docker_generating_docker',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build -t doc_task_generation__%s_%s .' % (rosdistro_name, doc_repo_spec.name),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - generating doc task"',
        'rm -fr $WORKSPACE/docker_doc',
        'mkdir -p $WORKSPACE/docker_doc',
        'docker run' +
        ' --cidfile=$WORKSPACE/docker_generating_docker/docker.cid' +
        ' -e=HOME=/home/buildfarm' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/rosdoc_lite:/tmp/rosdoc_lite:ro' +
        ' -v $WORKSPACE/catkin-sphinx:/tmp/catkin-sphinx:ro' +
        ' -v $WORKSPACE/rosdoc_index:/tmp/rosdoc_index:ro' +
        ' -v $WORKSPACE/catkin_workspace:/tmp/catkin_workspace' +
        ' -v $WORKSPACE/generated_documentation:/tmp/generated_documentation' +
        ' -v $WORKSPACE/docker_doc:/tmp/docker_doc' +
        ' doc_task_generation__%s_%s' % (rosdistro_name, doc_repo_spec.name),
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'if [ ! -f "$WORKSPACE/docker_doc/Dockerfile" ]; then',
        '  exit 0',
        'fi',
        '',
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ --cid-file $WORKSPACE/docker_doc/docker.cid > $WORKSPACE/docker_doc/subprocess_reaper.log 2>&1 &',
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - doc"',
        '# build and run build_and_install Dockerfile',
        'cd $WORKSPACE/docker_doc',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build -t doc__%s_%s .' % (rosdistro_name, doc_repo_spec.name),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - doc"',
        'docker run' +
        ' --cidfile=$WORKSPACE/docker_doc/docker.cid' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/rosdoc_lite:/tmp/rosdoc_lite:ro' +
        ' -v $WORKSPACE/catkin-sphinx:/tmp/catkin-sphinx:ro' +
        ' -v $WORKSPACE/rosdoc_index:/tmp/rosdoc_index:ro' +
        ' -v $WORKSPACE/catkin_workspace:/tmp/catkin_workspace' +
        ' -v $WORKSPACE/generated_documentation:/tmp/generated_documentation' +
        ' doc__%s_%s' % (rosdistro_name, doc_repo_spec.name),
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'if [ "$skip_cleanup" = "false" ]; then',
        'echo "# BEGIN SECTION: Clean up to save disk space on slaves"',
        'rm -fr catkin_workspace/build_isolated',
        'rm -fr catkin_workspace/devel_isolated',
        'rm -fr catkin_workspace/install_isolated',
        'rm -fr rosdoc_index',
        'echo "# END SECTION"',
        'fi',
    ]),
))@
@(SNIPPET(
    'builder_publish-over-ssh',
    config_name='docs',
    remote_directory=rosdistro_name,
    source_files=[
        'generated_documentation/api/**/stamp',
        'generated_documentation/changelogs/**/*.html',
        'generated_documentation/symbols/*.tag',

        'generated_documentation/deps/*',
        'generated_documentation/hashes/*',
        'generated_documentation/locations/*',
        'generated_documentation/metapackage_deps/*',
    ],
    remove_prefix='generated_documentation',
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'if [ -d "$WORKSPACE/generated_documentation/api_rosdoc" ]; then',
        '  echo "# BEGIN SECTION: rsync API documentation to server"',
        '  cd $WORKSPACE/generated_documentation/api_rosdoc',
        '  for pkg_name in $(find . -maxdepth 1 -mindepth 1 -type d); do',
        '    rsync -e "ssh -o StrictHostKeyChecking=no" -r --delete $pkg_name jenkins-slave@repo:/var/repos/docs/%s/api' % rosdistro_name,
        '  done',
        '  echo "# END SECTION"',
        'fi',
    ]),
))@
  </builders>
  <publishers>
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
    'build-wrapper_ssh-agent',
    credential_id=credential_id,
))@
  </buildWrappers>
</project>
