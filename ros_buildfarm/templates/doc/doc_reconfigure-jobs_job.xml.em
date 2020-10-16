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
    priority=30,
))@
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
            'name': 'dry_run',
            'description': 'Skip the actual reconfiguration but show the diffs',
        },
        {
            'type': 'string',
            'name': 'repository_names',
            'description': 'Only reconfigure the jobs of specific repositories',
        },
    ],
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
  <assignedNode>agent_on_master</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers>
@(SNIPPET(
    'trigger_timer',
    spec='0 23 * * *',
))@
  </triggers>
  <concurrentBuild>false</concurrentBuild>
  <builders>
@(SNIPPET(
    'builder_system-groovy',
    command=
"""// USE PARAMETER FOR BUILD DESCRIPTION
repository_names = build.buildVariableResolver.resolve('repository_names')
if (repository_names) {
  build.setDescription(repository_names)
}
""",
    script_file=None,
))@
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
        'rm -fr $WORKSPACE/docker_generate_doc_jobs',
        'rm -fr $WORKSPACE/reconfigure_jobs',
        'mkdir -p $WORKSPACE/docker_generate_doc_jobs',
        'mkdir -p $WORKSPACE/reconfigure_jobs',
        '',
        '# monitor all subprocesses and enforce termination',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/subprocess_reaper.py $$ --cid-file $WORKSPACE/docker_generate_doc_jobs/docker.cid > $WORKSPACE/docker_generate_doc_jobs/subprocess_reaper.log 2>&1 &',
        '# sleep to give python time to startup',
        'sleep 1',
        '',
        '# generate Dockerfile, build and run it',
        '# generating the Dockerfiles for the actual doc tasks',
        'echo "# BEGIN SECTION: Generate Dockerfile - reconfigure jobs"',
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        'if [ "$dry_run" = "true" ]; then DRY_RUN_FLAG="--dry-run"; fi',
        'if [ "$repository_names" != "" ]; then REPOSITORY_NAMES_FLAG="--repository-names $repository_names"; fi',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/doc/run_doc_reconfigure_job.py' +
        ' ' + config_url +
        ' ' + rosdistro_name +
        ' ' + doc_build_name +
        ' ' + ' '.join(repository_args) +
        ' --groovy-script /tmp/reconfigure_jobs/reconfigure_jobs.groovy' +
        ' --dockerfile-dir $WORKSPACE/docker_generate_doc_jobs' +
        ' $DRY_RUN_FLAG' +
        ' $REPOSITORY_NAMES_FLAG',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Build Dockerfile - reconfigure jobs"',
        'cd $WORKSPACE/docker_generate_doc_jobs',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/misc/docker_pull_baseimage.py',
        'docker build --force-rm -t doc_reconfigure_jobs .',
        'echo "# END SECTION"',
        '',
        'echo "# BEGIN SECTION: Run Dockerfile - reconfigure jobs"',
        '# -e=GIT_BRANCH= is required since Jenkins leaves the wc in detached state',
        'docker run' +
        ' --rm ' +
        ' --cidfile=$WORKSPACE/docker_generate_doc_jobs/docker.cid' +
        ' -e=GIT_BRANCH=$GIT_BRANCH' +
        ' --net=host' +
        ' -v $WORKSPACE/ros_buildfarm:/tmp/ros_buildfarm:ro' +
        ' -v %s:%s:ro' % (credentials_src, credentials_dst) +
        ' -v $WORKSPACE/reconfigure_jobs:/tmp/reconfigure_jobs' +
        ' doc_reconfigure_jobs',
        'echo "# END SECTION"',
    ]),
))@
@(SNIPPET(
    'builder_system-groovy',
    command=None,
    script_file='$WORKSPACE/reconfigure_jobs/reconfigure_jobs.groovy',
))@
  </builders>
  <publishers>
@(SNIPPET(
    'publisher_mailer',
    recipients=recipients,
    dynamic_recipients=[],
    send_to_individuals=False,
))@
  </publishers>
  <buildWrappers>
@(SNIPPET(
    'build-wrapper_timestamper',
))@
  </buildWrappers>
</project>
