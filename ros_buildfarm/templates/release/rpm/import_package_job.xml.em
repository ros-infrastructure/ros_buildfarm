<project>
  <actions/>
  <description>Generated at @ESCAPE(now_str) from template '@ESCAPE(template_name)'</description>
  <keepDependencies>false</keepDependencies>
  <properties>
@(SNIPPET(
    'property_log-rotator',
    days_to_keep=30,
    num_to_keep=10000,
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
    'property_parameters-definition',
    parameters=[
        {
            'type': 'string',
            'name': 'DISTRIBUTION_NAME',
        },
        {
            'type': 'string',
            'name': 'PULP_RESOURCES',
        },
        {
            'type': 'boolean',
            'name': 'INVALIDATE_DOWNSTREAM',
        },
        {
            'type': 'string',
            'name': 'INVALIDATE_EXPRESSION',
        },
        {
            'type': 'boolean',
            'name': 'DRY_RUN',
            'description': 'Skip the commit operation but show what would change',
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
  <assignedNode>building_repository</assignedNode>
  <canRoam>false</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenDownstreamBuilding>false</blockBuildWhenDownstreamBuilding>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
@(SNIPPET(
    'builder_shell',
    script='\n'.join([
        'echo "# BEGIN SECTION: import RPM package"',
        'if [ "$INVALIDATE_DOWNSTREAM" = "true" ]; then INVALIDATE_ARG=--invalidate; fi',
        'if [ "$DRY_RUN" = "true" ]; then DRY_RUN_ARG="--dry-run"; fi',
        'if [ "$INVALIDATE_EXPRESSION" != "" ]; then INVALIDATE_EXPRESSION_ARG="--invalidate-expression $INVALIDATE_EXPRESSION"; fi',
        'export PYTHONPATH=$WORKSPACE/ros_buildfarm:$PYTHONPATH',
        'python3 -u $WORKSPACE/ros_buildfarm/scripts/release/rpm/import_package.py' +
        ' --pulp-distribution-name $DISTRIBUTION_NAME' +
        ' $PULP_RESOURCES' +
        ' $INVALIDATE_ARG' +
        ' $INVALIDATE_EXPRESSION_ARG' +
        ' $DRY_RUN_ARG',
        'echo "# END SECTION"',
    ]),
))@
  </builders>
  <publishers>
@(SNIPPET(
    'publisher_description-setter',
    regexp='Importing package: (\S+)',
    # to prevent overwriting the description of failed builds
    regexp_for_failed='ThisRegExpShouldNeverMatch',
))@
@(SNIPPET(
    'publisher_extended-email',
    recipients=notify_emails,
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
