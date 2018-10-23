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
    'property_requeue-job',
))@
  </properties>
@(SNIPPET(
  'scm_git',
   url=upload_repository_url,
   branch_name=upload_repository_branch,
   git_ssh_credential_id=upload_credential_id,
   relative_target_dir='upload_repository',
   refspec=None,
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
@[for doc_repository_url in doc_repositories]@
@{
import os
doc_repository_name = os.path.splitext(os.path.basename(doc_repository_url))[0]
}@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Clone %s"' % doc_repository_name,
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/wrapper/git.py clone --depth 1 %s $WORKSPACE/repositories/%s' % (doc_repository_url, doc_repository_name),
        'git -C $WORKSPACE/repositories/%s log -n 1' % doc_repository_name,
        'rm -fr $WORKSPACE/repositories/%s/.git' % doc_repository_name,
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
@[end for]@
  </builders>
  <publishers>
@(SNIPPET(
    'publisher_mailer',
    recipients=notify_emails,
    dynamic_recipients=[],
    send_to_individuals=False,
))@
@(SNIPPET(
    'publisher_publish-over-git',
    branch=upload_repository_branch
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
  </buildWrappers>
</project>
