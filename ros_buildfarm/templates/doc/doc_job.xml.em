@{import os}@
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
    days_to_keep=365,
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
    'property_job-weight',
))@
  </properties>
@(SNIPPET(
    'scm',
    repo_spec=doc_repo_spec,
    path='ws/src/%s' % doc_repo_spec.name,
    git_ssh_credential_id=git_ssh_credential_id,
))@
  <scmCheckoutRetryCount>2</scmCheckoutRetryCount>
  <assignedNode>@(node_label)</assignedNode>
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
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Clone rosdoc2"',
        'rm -fr rosdoc2',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/wrapper/git.py clone --depth 1 https://github.com/ros-infrastructure/rosdoc2.git rosdoc2',
        'git -C rosdoc2 log -n 1',
        'rm -fr rosdoc2/doc',
        'echo "# END SECTION"',
#        '',
#        'echo "# BEGIN SECTION: Clone exhale"',
#        'rm -fr exhale',
#        'python3 -u $WORKSPACE/ros_buildfarm/scripts/wrapper/git.py clone --depth 1 https://github.com/wjwwood/exhale exhale',
#        'git -C exhale log -n 1',
#        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
# TODO(wjwwood): need to rsync tag files and object files, once we know where it will be
#        'echo "# BEGIN SECTION: rsync (most of) the rosdoc_index to agent"',
#        'rm -fr rosdoc_index',
#        'mkdir rosdoc_index',
#        '# since rsync fails if the source folder does not exist we need to check it before',
#        'if ssh %s@%s stat %s/%s > /dev/null 2> /dev/null; then' % \
#          (upload_user, upload_host, upload_root.rstrip('/'), rosdistro_name),
#        '  rsync -e ssh --stats' +
#        ' --prune-empty-dirs --recursive' +
#        ' --include="*/"' +
#        ' --include="api/*/manifest.yaml"' +
#        ' --include="deps/*"' +
#        ' --include="hashes/%s"' % doc_repo_spec.name +
#        ' --include="locations/*"' +
#        ' --include="metapackage_deps/*"' +
#        ' --include="symbols/*"' +
#        ' --exclude="*"' +
#        ' %s@%s:%s/%s $WORKSPACE/rosdoc_index' % \
#          (upload_user, upload_host, upload_root.rstrip('/'), rosdistro_name),
#        'fi',
#        'echo "# END SECTION"',
    ]),
))@

<!-- Begin transplant from devel job -->
<!-- (wjwwood) We have to build (but not test) the packages before documenting them -->
<!-- TODO(wjwwood): should we de-duplicate this from devel job? -->

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

<!-- End transplant from devel job -->

@(SNIPPET(
    'builder_shell_key-files',
    script_generating_key_files=script_generating_key_files,
))@
@{
if doc_repo_spec.type == 'hg':
    hgcache_mount_arg = ' -v $HOME/hgcache:$HOME/hgcache '
else:
    hgcache_mount_arg = ''
}@
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
        ' --build-tool ' + build_tool +
        ' --vcs-info "%s %s %s"' % (doc_repo_spec.type, doc_repo_spec.version if doc_repo_spec.version is not None else '', doc_repo_spec.url) +
        ' ' + ' '.join(repository_args) +
        ' $FORCE_FLAG' +
        ' --dockerfile-dir $WORKSPACE/docker_generating_docker',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - generating doc task"',
        'cd $WORKSPACE/docker_generating_docker',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build --force-rm -t doc_task_generation.%s_%s .' % (rosdistro_name, doc_repo_spec.name.lower()),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - generating doc task"',
        'rm -fr $WORKSPACE/docker_doc',
        'mkdir -p $WORKSPACE/docker_doc',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_generating_docker/docker.cid' +
        ' -e=HOME=/home/buildfarm' +
        ' -e=TRAVIS=$TRAVIS' +
        ' -e=ROS_BUILDFARM_PULL_REQUEST_BRANCH=$ROS_BUILDFARM_PULL_REQUEST_BRANCH' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/rosdoc_lite:/tmp/rosdoc_lite:ro' +
        ' -v $WORKSPACE/catkin-sphinx:/tmp/catkin-sphinx:ro' +
        ' -v $WORKSPACE/rosdoc_index:/tmp/rosdoc_index:ro' +
        ' -v $WORKSPACE/ws:/tmp/ws' +
        ' -v $WORKSPACE/generated_documentation:/tmp/generated_documentation' +
        ' -v $WORKSPACE/docker_doc:/tmp/docker_doc' +
        hgcache_mount_arg +
        ' doc_task_generation.%s_%s' % (rosdistro_name, doc_repo_spec.name.lower()),
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
        'docker build --force-rm -t doc.%s_%s .' % (rosdistro_name, doc_repo_spec.name.lower()),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - doc"',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_doc/docker.cid' +
        ' -e=TRAVIS=$TRAVIS' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/rosdoc_lite:/tmp/rosdoc_lite:ro' +
        ' -v $WORKSPACE/catkin-sphinx:/tmp/catkin-sphinx:ro' +
        ' -v $WORKSPACE/rosdoc_index:/tmp/rosdoc_index:ro' +
        ' -v $WORKSPACE/ws:/tmp/ws' +
        ' -v $WORKSPACE/generated_documentation:/tmp/generated_documentation' +
        ' doc.%s_%s' % (rosdistro_name, doc_repo_spec.name.lower()),
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
        'rm -fr exhale',
        'rm -fr rosdoc2_index',
        'rm -fr rosdoc2',
        'echo "# END SECTION"',
        'fi',
    ]),
))@
@(SNIPPET(
    'builder_publish-over-ssh',
    config_name='docs',
    remote_directory=rosdistro_name,
    source_files=[
        'generated_documentation/api/**/manifest.yaml',
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
# TODO(wjwwood): update with new location when I know it
#        'if [ -d "$WORKSPACE/generated_documentation/api_rosdoc" ]; then',
#        '  echo "# BEGIN SECTION: rsync API documentation to server"',
#        '  cd $WORKSPACE/generated_documentation/api_rosdoc',
#        '  for pkg_name in $(find . -maxdepth 1 -mindepth 1 -type d); do',
#        '    rsync -e ssh --stats -r --delete $pkg_name %s@%s:%s' % \
#          (upload_user, upload_host, os.path.join(upload_root, rosdistro_name, 'api')),
#        '  done',
#        '  echo "# END SECTION"',
#        'fi',
    ]),
))@
@(SNIPPET(
    'builder_system-groovy_extract-warnings',
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
    credential_ids=[credential_id],
))@
  </buildWrappers>
</project>
