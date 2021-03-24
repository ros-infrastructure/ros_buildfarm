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
    os_name={'rhel': 'centos'}.get(os_name, os_name),
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
        'rm -fr $WORKSPACE/docker_binaryrpm',
        'mkdir -p $WORKSPACE/docker_binaryrpm',
        '',
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ --cid-file $WORKSPACE/docker_binaryrpm/docker.cid > $WORKSPACE/docker_binaryrpm/subprocess_reaper.log 2>&1 &',
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        '# generate Dockerfile, build and run it',
        '# generating the Dockerfile for the actual binaryrpm task',
        'echo "# BEGIN SECTION: Generate Dockerfile - binaryrpm task"',
        'export TZ="%s"' % timezone,
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/release/rpm/run_binarypkg_job.py' +
        ' --rosdistro-index-url ' + rosdistro_index_url +
        ' ' + rosdistro_name +
        ' ' + pkg_name +
        ' ' + os_name +
        ' ' + os_code_name +
        ' ' + arch +
        ' ' + ' '.join(repository_args) +
        ' --dockerfile-dir $WORKSPACE/docker_binaryrpm' +
        ' --binarypkg-dir /tmp/binarypkg' +
        ' --env-vars ' + ' '.join(build_environment_variables) +
        (' --append-timestamp' if append_timestamp else ''),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - build binaryrpm"',
        'cd $WORKSPACE/docker_binaryrpm',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build --force-rm -t binaryrpm.%s_%s_%s_%s_%s .' % (rosdistro_name, os_name, os_code_name, arch, pkg_name),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - build binaryrpm"',
        'rm -fr $WORKSPACE/binarypkg',
        'mkdir -p $WORKSPACE/binarypkg/source',
    ] + ([
        'if [ ! -d "$HOME/.ccache" ]; then mkdir $HOME/.ccache; fi',
    ] if shared_ccache else []) + [
        'docker run' +
        ' --rm' +
        ' --privileged' +
        ' --cidfile=$WORKSPACE/docker_binaryrpm/docker.cid' +
        ' -e=TRAVIS=$TRAVIS' +
        ' --net=host' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/binarypkg:/tmp/binarypkg' +
        (' -v $HOME/.ccache:/home/buildfarm/.ccache' if shared_ccache else '') +
        ' binaryrpm.%s_%s_%s_%s_%s' % (rosdistro_name, os_name, os_code_name, arch, pkg_name),
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Upload binaryrpm"',
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        "ls binarypkg/*.rpm | grep -v -e 'src\.rpm$' -e '-debug\(info\|source\)-' > binarypkg/upload_list.txt && " +
        'xargs -a binarypkg/upload_list.txt' +
        ' python3 -u $WORKSPACE/ros_buildfarm/scripts/release/rpm/upload_package.py' +
        ' --pulp-resource-record binarypkg/upload_record.txt',
        'echo "# END SECTION"',
        'echo "# BEGIN SECTION: Upload debug symbols"',
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        "ls binarypkg/*.rpm | grep -e '-debug\(info\|source\)-' > binarypkg/upload_list_debug.txt && " +
        'xargs -a binarypkg/upload_list_debug.txt' +
        ' python3 -u $WORKSPACE/ros_buildfarm/scripts/release/rpm/upload_package.py' +
        ' --pulp-resource-record binarypkg/upload_record_debug.txt',
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_parameterized-trigger',
    project=import_package_job_name,
    parameters='\n'.join([
        'DISTRIBUTION_NAME=ros-building-%s-%s-%s' % (
            os_name, os_code_name, arch),
        'INVALIDATE_DOWNSTREAM=true']),
    parameter_files=['binarypkg/upload_record.txt'],
    continue_on_failure=False,
))@
@(SNIPPET(
    'builder_parameterized-trigger',
    project=import_package_job_name,
    parameters='\n'.join([
        'DISTRIBUTION_NAME=ros-building-%s-%s-%s-debug' % (
            os_name, os_code_name, arch),
        'INVALIDATE_DOWNSTREAM=false']),
    parameter_files=['binarypkg/upload_record_debug.txt'],
    continue_on_failure=False,
    missing_parameter_files_skip=True,
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'if [ "$skip_cleanup" = "false" ]; then',
        'echo "# BEGIN SECTION: Clean up to save disk space on agents"',
        'rm -f binarypkg/*.rpm binarypkg/source/*.rpm',
        'echo "# END SECTION"',
        'fi',
    ]),
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
@(SNIPPET(
    'pulp_credentials',
    credential_id=credential_id,
    dest_credential_id=dest_credential_id,
))@
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
