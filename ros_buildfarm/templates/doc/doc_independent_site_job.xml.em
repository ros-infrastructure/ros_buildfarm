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
   relative_target_dir='site',
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
    script='rm -fr $WORKSPACE/repository',
))@
@(SNIPPET(
    'builder_shell_key-files',
    script_generating_key_files=script_generating_key_files,
))@
@{
import os
doc_repository_name = os.path.splitext(os.path.basename(doc_repository_url))[0]
}@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Clone %s"' % doc_repository_name,
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/wrapper/git.py clone --depth 1 %s $WORKSPACE/repository' % doc_repository_url,
        'git -C $WORKSPACE/repository log -n 1',
        'rm -fr $WORKSPACE/repository/.git',
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'rm -fr $WORKSPACE/docker_site',
        'mkdir -p $WORKSPACE/docker_site',
        '',
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ --cid-file $WORKSPACE/docker_site/docker.cid > $WORKSPACE/docker_generating_docker/docker_site.log 2>&1 &',
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        'echo "# BEGIN SECTION: Build site environment - %s"' % doc_repository_name,
        'cd $WORKSPACE/repository',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py docker/image/Dockerfile',
        'docker build --force-rm -f docker/image/Dockerfile' +
        ' --build-arg user=`whoami` --build-arg uid=`id -u`' +
        ' -t %s-env .' % doc_repository_name,
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build & update site - %s"' % doc_repository_name,
        'docker run' +
        ' --rm' +
        ' --net=host' +
        ' --cidfile=$WORKSPACE/docker_site/docker.cid' +
        ' -v $WORKSPACE/repository:/tmp/scaffold' +
        ' -v $WORKSPACE/site:/tmp/site' +
        ' %s-env update_site /tmp/scaffold /tmp/site' % doc_repository_name,
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
