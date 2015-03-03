<project>
  <actions/>
  <description>Generated at @ESCAPE(now_str) from template '@ESCAPE(template_name)'</description>
@(SNIPPET(
    'log-rotator',
    days_to_keep=100,
    num_to_keep=100,
))@
  <keepDependencies>false</keepDependencies>
  <properties>
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
    'scm_null',
))@
  <assignedNode>@(node_label if node_label else 'buildslave')</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers>
@(SNIPPET(
    'trigger_poll',
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
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Clone ros_buildfarm"',
        'rm -fr ros_buildfarm',
        'git clone --depth 1 %s%s ros_buildfarm' % ('-b %s ' % ros_buildfarm_repository.version if ros_buildfarm_repository.version else '', ros_buildfarm_repository.url),
        'git -C ros_buildfarm log -n 1',
        'rm -fr ros_buildfarm/.git',
        'rm -fr ros_buildfarm/doc',
        'echo "# END SECTION"',
        'rm -fr repositories',
    ]),
))@
@[for repo_url in doc_repositories]@
@{
import os
repo_name = os.path.splitext(os.path.basename(repo_url))[0]
}@
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: Clone %s"' % repo_name,
        'git clone --depth 1 %s $WORKSPACE/repositories/%s' % (repo_url, repo_name),
        'git -C $WORKSPACE/repositories/%s log -n 1' % repo_name,
        'rm -fr $WORKSPACE/repositories/%s/.git' % repo_name,
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
        ' ' + ' '.join(repository_args) +
        ' --dockerfile-dir $WORKSPACE/docker_doc_independent',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - doc independent"',
        'cd $WORKSPACE/docker_doc_independent',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build -t doc_independent .',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - doc independent"',
        'docker run' +
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
        '  ssh jenkins-slave@repo "mkdir -p /var/repos/docs/independent/api"',
        '  cd $WORKSPACE/generated_documentation/independent/api',
        '  for pkg_name in $(find . -maxdepth 1 -mindepth 1 -type d); do',
        '    rsync -e "ssh -o StrictHostKeyChecking=no" -r --delete $pkg_name/html jenkins-slave@repo:/var/repos/docs/independent/api/$pkg_name',
        '  done',
        '  echo "# END SECTION"',
        'fi',
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
    credential_id=credential_id,
))@
  </buildWrappers>
</project>
