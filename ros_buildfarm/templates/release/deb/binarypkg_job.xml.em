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
  <triggers>
@[if upstream_projects]@
@(SNIPPET(
    'trigger_reverse-build',
    upstream_projects=upstream_projects,
))@
@[end if]@
  </triggers>
  <concurrentBuild>false</concurrentBuild>
  <builders>
@(SNIPPET(
    'builder_system-groovy_verify-upstream',
))@
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
        'rm -fr $WORKSPACE/docker_generating_docker',
        'mkdir -p $WORKSPACE/docker_generating_docker',
        '',
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ --cid-file $WORKSPACE/docker_generating_docker/docker.cid > $WORKSPACE/docker_generating_docker/subprocess_reaper.log 2>&1 &',
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        '# generate Dockerfile, build and run it',
        '# generating the Dockerfile for the actual binarydeb task',
        'echo "# BEGIN SECTION: Generate Dockerfile - binarydeb task"',
        'export TZ="%s"' % timezone,
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/release/run_binarydeb_job.py' +
        ' --rosdistro-index-url ' + rosdistro_index_url +
        ' ' + rosdistro_name +
        ' ' + pkg_name +
        ' ' + os_name +
        ' ' + os_code_name +
        ' ' + arch +
        ' ' + ' '.join(repository_args) +
        ' --binarypkg-dir /tmp/binarydeb' +
        ' --dockerfile-dir $WORKSPACE/docker_generating_docker' +
        ' --env-vars ' + ' '.join(build_environment_variables) +
        (' --append-timestamp' if append_timestamp else ''),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - binarydeb task"',
        'cd $WORKSPACE/docker_generating_docker',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build --force-rm -t binarydeb_task_generation.%s_%s_%s_%s_%s .' % (rosdistro_name, os_name, os_code_name, arch, pkg_name),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - binarydeb task"',
        '# ensure to have write permission before trying to delete the folder',
        'if [ -f $WORKSPACE/binarydeb ] ; then chmod -R u+w $WORKSPACE/binarydeb ; fi',
        'rm -fr $WORKSPACE/binarydeb',
        'rm -fr $WORKSPACE/docker_build_binarydeb',
        'mkdir -p $WORKSPACE/binarydeb',
        'mkdir -p $WORKSPACE/docker_build_binarydeb',
    ] + ([
        'if [ ! -d "$HOME/.ccache" ]; then mkdir $HOME/.ccache; fi',
    ] if shared_ccache else []) + [
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_generating_docker/docker.cid' +
        ' -e=TRAVIS=$TRAVIS' +
        ' -e=ROS_BUILDFARM_PULL_REQUEST_BRANCH=$ROS_BUILDFARM_PULL_REQUEST_BRANCH' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/binarydeb:/tmp/binarydeb' +
        ' -v $WORKSPACE/docker_build_binarydeb:/tmp/docker_build_binarydeb' +
        (' -v $HOME/.ccache:/home/buildfarm/.ccache' if shared_ccache else '') +
        ' binarydeb_task_generation.%s_%s_%s_%s_%s' % (rosdistro_name, os_name, os_code_name, arch, pkg_name),
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ --cid-file $WORKSPACE/docker_build_binarydeb/docker.cid > $WORKSPACE/docker_build_binarydeb/subprocess_reaper.log 2>&1 &',
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - build binarydeb"',
        '# build and run build_binarydeb Dockerfile',
        'cd $WORKSPACE/docker_build_binarydeb',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build --force-rm -t binarydeb_build.%s_%s_%s_%s_%s .' % (rosdistro_name, os_name, os_code_name, arch, pkg_name),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - build binarydeb"',
        '# -e=HOME= is required to set a reasonable HOME for the user (not /)',
        '# otherwise apt-src will fail',
    ] + ([
        'if [ ! -d "$HOME/.ccache" ]; then mkdir $HOME/.ccache; fi',
    ] if shared_ccache else []) + [
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_build_binarydeb/docker.cid' +
        ' -e=HOME=' +
        ' -e=TRAVIS=$TRAVIS' +
        ' --net=host' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/binarydeb:/tmp/binarydeb' +
        (' -v $HOME/.ccache:/home/buildfarm/.ccache' if shared_ccache else '') +
        ' binarydeb_build.%s_%s_%s_%s_%s' % (rosdistro_name, os_name, os_code_name, arch, pkg_name),
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'if [ "$skip_cleanup" = "false" ]; then',
        'echo "# BEGIN SECTION: Clean up to save disk space on agents"',
        '# ensure to have write permission before trying to delete the folder',
        'chmod -R u+w $WORKSPACE/binarydeb',
        'rm -fr binarydeb/*/*',
        'echo "# END SECTION"',
        'fi',
    ]),
))@
@# disable installation check due to huge performance hit
@# @(SNIPPET(
@#     'builder_shell',
@#     script='\n'.join([
@#         'rm -fr $WORKSPACE/docker_install_binarydeb',
@#         'mkdir -p $WORKSPACE/docker_install_binarydeb',
@#         '',
@#         '# monitor all subprocesses and enforce termination',
@#         'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ --cid-file $WORKSPACE/docker_install_binarydeb/docker.cid > $WORKSPACE/docker_install_binarydeb/subprocess_reaper.log 2>&1 &',
@#         '# sleep to give python time to startup',
@#         'sleep 1',
@#         '',
@#         '# generate Dockerfile, build and run it',
@#         '# trying to install the built binarydeb',
@#         'echo "# BEGIN SECTION: Generate Dockerfile - install"',
@#         'export TZ="%s"' % timezone,
@#         'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
@#         'python3 -u $WORKSPACE/ros_buildfarm/scripts/release/create_binarydeb_install_task_generator.py' +
@#         ' ' + os_name +
@#         ' ' + os_code_name +
@#         ' ' + arch +
@#         ' ' + ' '.join(repository_args) +
@#         ' --binarypkg-dir $WORKSPACE/binarydeb' +
@#         ' --dockerfile-dir $WORKSPACE/docker_install_binarydeb',
@#         'echo "# END SECTION"',
@#         '',
@#         'echo "# BEGIN SECTION: Build Dockerfile - install"',
@#         'cd $WORKSPACE/docker_install_binarydeb',
@#         'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
@#         'docker build --force-rm -t binarydeb_install.%s_%s_%s_%s_%s .' % (rosdistro_name, os_name, os_code_name, arch, pkg_name),
@#         'echo "# END SECTION"',
@#         '',
@#         'echo "# BEGIN SECTION: Run Dockerfile - install"',
@#         'docker run' +
@#         ' --rm ' +
@#         ' --cidfile=$WORKSPACE/docker_install_binarydeb/docker.cid' +
@#         ' -e=TRAVIS=$TRAVIS' +
@#         ' -v $WORKSPACE/binarydeb:/tmp/binarydeb:ro' +
@#         ' binarydeb_install.%s_%s_%s_%s_%s' % (rosdistro_name, os_name, os_code_name, arch, pkg_name),
@#         'echo "# END SECTION"',
@#     ]),
@# ))@
@(SNIPPET(
    'builder_publish-over-ssh',
    config_name='repo',
    remote_directory='%s/${JOB_NAME}__${BUILD_NUMBER}' % os_code_name,
    source_files=binarydeb_files,
    remove_prefix='binarydeb',
))@
@(SNIPPET(
    'builder_parameterized-trigger',
    project=import_package_job_name,
    parameter_files=None,
    parameters='\n'.join([
        'subfolder=%s/${JOB_NAME}__${BUILD_NUMBER}' % os_code_name,
        'debian_package_name=%s' % debian_package_name]),
    continue_on_failure=False,
))@
  </builders>
  <publishers>
@(SNIPPET(
    'publisher_build-trigger',
    child_projects=child_projects,
))@
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
