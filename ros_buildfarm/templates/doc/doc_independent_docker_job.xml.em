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
@[if upload_repository_url is not None]@
@(SNIPPET(
  'scm_git',
   url=upload_repository_url,
   branch_name=upload_repository_branch,
   git_ssh_credential_id=upload_credential_id,
   relative_target_dir='upload_repository',
   refspec=None,
))@
@[else]@
@(SNIPPET(
    'scm_null',
))@
@[end if]@
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
    script='\n'.join([
      'rm -fr $WORKSPACE/repositories',
      'mkdir -p $WORKSPACE/repositories',
      'rm -fr $WORKSPACE/docker_containers',
      'mkdir -p $WORKSPACE/docker_containers',
      'rm -fr $WORKSPACE/docker_generating_docker',
      'mkdir -p $WORKSPACE/docker_generating_docker'
    ])
))@
@(SNIPPET(
    'builder_shell_key-files',
    script_generating_key_files=script_generating_key_files,
))@
@[for doc_repository_url,branch in doc_repositories.items()]@
@{
import os
doc_repository_name = os.path.splitext(os.path.basename(doc_repository_url))[0]

if not branch:
  repo_branch_arg = ''
else:
  repo_branch_arg = '--no-single-branch -b ' + branch
}@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Clone %s"' % doc_repository_name,
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/wrapper/git.py clone --depth 1 %s %s $WORKSPACE/repositories/%s' % (doc_repository_url, repo_branch_arg, doc_repository_name),
        'git -C $WORKSPACE/repositories/%s log -n 1' % doc_repository_name,
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py' +
        ' $$ --cid-file $WORKSPACE/docker_containers/docker_%s.cid >' % doc_repository_name +
        ' $WORKSPACE/docker_generating_docker/docker_%s.log 2>&1 &' % doc_repository_name,
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - %s"' % doc_repository_name,
        'cd $WORKSPACE/repositories/%s' % doc_repository_name,
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py docker/image/Dockerfile',
        'docker build --force-rm -f docker/image/Dockerfile' +
        ' --build-arg user=`whoami` --build-arg uid=`id -u`' +
        ' -t %s .' % doc_repository_name,
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Docker - %s"' % doc_repository_name,
        'docker run' +
        ' --rm' +
        ' --net=host' +
        ' --cidfile=$WORKSPACE/docker_containers/docker_%s.cid' % doc_repository_name +
        ' -v $WORKSPACE/repositories/%s:/tmp/doc_repository' % doc_repository_name +
        ' -v $WORKSPACE/upload_repository:/tmp/upload_repository' +
        ' -e REPO=/tmp/doc_repository' +
        ' -e SITE=/tmp/upload_repository' +
        ' %s' % doc_repository_name,
        'echo "# END SECTION"',
    ]),
))@
@[if upload_host is not None]@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'if [ -d "$WORKSPACE/repositories/%s/build/html" ]; then' % doc_repository_name,
        '  echo "# BEGIN SECTION: rsync documentation to server"',
        '  ssh %s@%s "mkdir -p %s"' %
          (upload_user, upload_host, upload_root),
        '  cd $WORKSPACE/repositories/%s/build' % doc_repository_name,
        '  rsync -e ssh --stats -r --delete html/ %s@%s:%s' % \
          (upload_user, upload_host, upload_root),
        '  echo "# END SECTION"',
        'fi',
    ]),
))@
@[end if]@
@[end for]@
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
@[if upload_repository_url is not None]@
@(SNIPPET(
    'publisher_publish-over-git',
    branch=upload_repository_branch
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
@[if upload_host is not None]@
@(SNIPPET(
    'build-wrapper_ssh-agent',
    credential_ids=[upload_credential_id],
))@
@[end if]@
  </buildWrappers>
</project>
