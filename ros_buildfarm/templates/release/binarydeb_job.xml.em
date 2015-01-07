<project>
  <actions/>
  <description>Generated at @ESCAPE(now_str) from template '@ESCAPE(template_name)'</description>
@(SNIPPET(
    'log-rotator',
    days_to_keep=180,
    num_to_keep=30,
))@
  <keepDependencies>false</keepDependencies>
  <properties>
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
    'property_requeue-job',
))@
@(SNIPPET(
    'property_disk-usage',
))@
  </properties>
@(SNIPPET(
    'scm_null',
))@
  <assignedNode>buildslave</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
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
    'builder_shell',
    script='\n'.join([
        '# generate key files',
        'echo "# BEGIN SECTION: Generate key files"',
    ] + script_generating_key_files + [
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'rm -fr $WORKSPACE/docker_generating_docker',
        'mkdir -p $WORKSPACE/docker_generating_docker',
        '',
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ > $WORKSPACE/docker_generating_docker/subprocess_reaper.log 2>&1 &',
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
        ' --binarydeb-dir $WORKSPACE/binarydeb' +
        ' --dockerfile-dir $WORKSPACE/docker_generating_docker' +
        (' --append-timestamp' if append_timestamp else ''),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - binarydeb task"',
        'cd $WORKSPACE/docker_generating_docker',
        'docker build -t binarydeb_task_generation__%s_%s_%s_%s_%s .' % (rosdistro_name, os_name, os_code_name, arch, pkg_name),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - binarydeb task"',
        'rm -fr $WORKSPACE/binarydeb',
        'rm -fr $WORKSPACE/docker_build_binarydeb',
        'mkdir -p $WORKSPACE/binarydeb',
        'mkdir -p $WORKSPACE/docker_build_binarydeb',
        'docker run' +
        ' --cidfile=$WORKSPACE/docker_generating_docker/docker.cid' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/binarydeb:/tmp/binarydeb' +
        ' -v $WORKSPACE/docker_build_binarydeb:/tmp/docker_build_binarydeb' +
        ' binarydeb_task_generation__%s_%s_%s_%s_%s' % (rosdistro_name, os_name, os_code_name, arch, pkg_name),
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ > $WORKSPACE/docker_build_binarydeb/subprocess_reaper.log 2>&1 &',
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - build binarydeb"',
        '# build and run build_binarydeb Dockerfile',
        'cd $WORKSPACE/docker_build_binarydeb',
        'docker build -t binarydeb_build__%s_%s_%s_%s_%s .' % (rosdistro_name, os_name, os_code_name, arch, pkg_name),
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - build binarydeb"',
        '# -e=HOME= is required to set a reasonable HOME for the user (not /)',
        '# otherwise apt-src will fail',
        'docker run' +
        ' --cidfile=$WORKSPACE/docker_build_binarydeb/docker.cid' +
        ' -e=HOME=' +
        ' --net=host' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/binarydeb:/tmp/binarydeb' +
        ' binarydeb_build__%s_%s_%s_%s_%s' % (rosdistro_name, os_name, os_code_name, arch, pkg_name),
        'echo "# END SECTION"',
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
@#         'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ > $WORKSPACE/docker_install_binarydeb/subprocess_reaper.log 2>&1 &',
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
@#         ' --binarydeb-dir $WORKSPACE/binarydeb' +
@#         ' --dockerfile-dir $WORKSPACE/docker_install_binarydeb',
@#         'echo "# END SECTION"',
@#         '',
@#         'echo "# BEGIN SECTION: Build Dockerfile - install"',
@#         'cd $WORKSPACE/docker_install_binarydeb',
@#         'docker build -t binarydeb_install__%s_%s_%s_%s_%s .' % (rosdistro_name, os_name, os_code_name, arch, pkg_name),
@#         'echo "# END SECTION"',
@#         '',
@#         'echo "# BEGIN SECTION: Run Dockerfile - install"',
@#         'docker run' +
@#         ' --cidfile=$WORKSPACE/docker_install_binarydeb/docker.cid' +
@#         ' -v $WORKSPACE/binarydeb:/tmp/binarydeb:ro' +
@#         ' binarydeb_install__%s_%s_%s_%s_%s' % (rosdistro_name, os_name, os_code_name, arch, pkg_name),
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
    parameters='\n'.join([
        'subfolder=%s/${JOB_NAME}__${BUILD_NUMBER}' % os_code_name,
        'debian_package_name=%s' % debian_package_name]),
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
    regexp_for_failed='',
))@
@(SNIPPET(
    'publisher_groovy-postbuild_slave-low-disk-space',
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
    'build-wrapper_disk-check',
))@
@(SNIPPET(
    'build-wrapper_ssh-agent_credential-id',
))@
  </buildWrappers>
</project>
