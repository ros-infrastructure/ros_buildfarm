<project>
  <actions/>
  <description>Generated at @ESCAPE(now_str) from template '@ESCAPE(template_name)'</description>
  <keepDependencies>false</keepDependencies>
  <properties>
@(SNIPPET(
    'property_log-rotator',
    days_to_keep=365,
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
@(SNIPPET(
    'property_job-weight',
))@
  </properties>
@(SNIPPET(
    'scm_null',
))@
  <assignedNode>@(node_label)</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers>
@(SNIPPET(
    'trigger_timer',
    spec='H 3 * * *',
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
    os_name='ubuntu',
    os_code_name='xenial',
    arch='amd64',
))@
@(SNIPPET(
    'builder_shell_clone-ros-buildfarm',
    ros_buildfarm_repository=ros_buildfarm_repository,
    wrapper_scripts=wrapper_scripts,
))@
@(SNIPPET(
    'builder_shell',
    script='rm -fr repositories',
))@
@[for repo_url,branch in doc_repositories.items()]@
@{
import os
repo_name = os.path.splitext(os.path.basename(repo_url))[0]

if not branch:
  repo_branch_arg = ''
else:
  repo_branch_arg = '--no-single-branch -b ' + branch
}@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Clone %s"' % repo_name,
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/wrapper/git.py clone --depth 1 %s %s $WORKSPACE/repositories/%s' % (repo_url, repo_branch_arg, repo_name),
        'git -C $WORKSPACE/repositories/%s log -n 1' % repo_name,
        'echo "# END SECTION"',
    ]),
))@
@[end for]@
@(SNIPPET(
    'builder_shell_key-files',
    script_generating_key_files=script_generating_key_files,
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'rm -fr $WORKSPACE/docker_doc_independent',
        'rm -fr $WORKSPACE/generated_documentation',
        'mkdir -p $WORKSPACE/docker_doc_independent',
        'mkdir -p $WORKSPACE/generated_documentation',
        '',
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ --cid-file $WORKSPACE/docker_doc_independent/docker.cid > $WORKSPACE/docker_generating_docker/docker_doc_independent.log 2>&1 &',
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        '# generate Dockerfile, build and run it',
        '# generating documentation for independent packages',
        'echo "# BEGIN SECTION: Generate Dockerfile - doc independent task"',
        'export TZ="%s"' % timezone,
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/doc/run_doc_independent_job.py' +
        ' ' + config_url +
        ' ' + doc_build_name +
        ' --install-apt-packages ' + ' '.join(install_apt_packages) +
        ' --install-pip-packages ' + ' '.join(install_pip_packages) +
        ' ' + ' '.join(repository_args) +
        ' --dockerfile-dir $WORKSPACE/docker_doc_independent',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - doc independent"',
        'cd $WORKSPACE/docker_doc_independent',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build --force-rm -t doc_independent .',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - doc independent"',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_doc_independent/docker.cid' +
        ' -e=HOME=/home/buildfarm' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v $WORKSPACE/repositories:/tmp/repositories' +
        ' -v $WORKSPACE/generated_documentation:/tmp/generated_documentation' +
        ' doc_independent',
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'if [ -d "$WORKSPACE/generated_documentation/independent/api" ]; then',
        '  echo "# BEGIN SECTION: rsync API documentation to server"',
        '  ssh %s@%s "mkdir -p %s"' %
          (upload_user, upload_host, os.path.join(upload_root, 'independent', 'api')),
        '  cd $WORKSPACE/generated_documentation/independent/api',
        '  for pkg_name in $(find . -maxdepth 1 -mindepth 1 -type d); do',
        '    rsync -e ssh --stats -r --delete $pkg_name/html %s@%s:%s' % \
          (upload_user, upload_host, os.path.join(upload_root, 'independent/api/$pkg_name')),
        '  done',
        '  echo "# END SECTION"',
        'fi',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Clean up to save disk space on agents"',
        '# ensure to have write permission before trying to delete the folder',
        'chmod -R u+w $WORKSPACE/repositories',
        'rm -fr $WORKSPACE/repositories',
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
    credential_ids=[upload_credential_id],
))@
  </buildWrappers>
</project>
