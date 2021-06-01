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
        'echo "# BEGIN SECTION: sync packages to testing repos"',
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/release/rpm/sync_repo.py' +
        ' --distribution-source-expression "^ros-building-%s-%s-(SRPMS|%s(-debug)?)$"' % (os_name, os_code_name, arch) +
        ' --distribution-dest-expression "^ros-testing-%s-%s-\\1$"' % (os_name, os_code_name) +
        ' --package-name-expression "^ros-%s-.*"' % rosdistro_name +
        ' --invalidate-expression "^ros-%s-.*"' % rosdistro_name,
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: mirror testing repository content to disk"',
        'rsync --recursive --times --delete --itemize-changes rsync://127.0.0.1:1234/ros-testing-%s-%s-SRPMS/ /var/repos/%s/testing/%s/SRPMS/' % (os_name, os_code_name, os_name, os_code_name),
        'rsync --recursive --times --delete --exclude=debug --itemize-changes rsync://127.0.0.1:1234/ros-testing-%s-%s-%s/ /var/repos/%s/testing/%s/%s/' % (os_name, os_code_name, arch, os_name, os_code_name, arch),
        'rsync --recursive --times --delete --itemize-changes rsync://127.0.0.1:1234/ros-testing-%s-%s-%s-debug/ /var/repos/%s/testing/%s/%s/debug/' % (os_name, os_code_name, arch, os_name, os_code_name, arch),
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
    'pulp_credentials',
    credential_id=credential_id,
    dest_credential_id=dest_credential_id,
))@
@(SNIPPET(
    'build-wrapper_timestamper',
))@
  </buildWrappers>
</project>
