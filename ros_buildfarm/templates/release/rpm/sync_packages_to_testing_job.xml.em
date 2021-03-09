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
    'builder_shell',
    script='\n'.join([
        '# generate key files',
        'echo "# BEGIN SECTION: Write PGP repository keys"',
        'mkdir -p $WORKSPACE/keys',
        'rm -fr $WORKSPACE/keys/*',
        'echo "-----BEGIN PGP PUBLIC KEY BLOCK-----\nVersion: GnuPG v1\n\n\nmQINBFzvJpYBEADY8l1YvO7iYW5gUESyzsTGnMvVUmlV3XarBaJz9bGRmgPXh7jc\nVFrQhE0L/HV7LOfoLI9H2GWYyHBqN5ERBlcA8XxG3ZvX7t9nAZPQT2Xxe3GT3tro\nu5oCR+SyHN9xPnUwDuqUSvJ2eqMYb9B/Hph3OmtjG30jSNq9kOF5bBTk1hOTGPH4\nK/AY0jzT6OpHfXU6ytlFsI47ZKsnTUhipGsKucQ1CXlyirndZ3V3k70YaooZ55rG\naIoAWlx2H0J7sAHmqS29N9jV9mo135d+d+TdLBXI0PXtiHzE9IPaX+ctdSUrPnp+\nTwR99lxglpIG6hLuvOMAaxiqFBB/Jf3XJ8OBakfS6nHrWH2WqQxRbiITl0irkQoz\npwNEF2Bv0+Jvs1UFEdVGz5a8xexQHst/RmKrtHLct3iOCvBNqoAQRbvWvBhPjO/p\nV5cYeUljZ5wpHyFkaEViClaVWqa6PIsyLqmyjsruPCWlURLsQoQxABcL8bwxX7UT\nhM6CtH6tGlYZ85RIzRifIm2oudzV5l+8oRgFr9yVcwyOFT6JCioqkwldW52P1pk/\n/SnuexC6LYqqDuHUs5NnokzzpfS6QaWfTY5P5tz4KHJfsjDIktly3mKVfY0fSPVV\nokdGpcUzvz2hq1fqjxB6MlB/1vtk0bImfcsoxBmF7H+4E9ZN1sX/tSb0KQARAQAB\ntCZPcGVuIFJvYm90aWNzIDxpbmZvQG9zcmZvdW5kYXRpb24ub3JnPokCVAQTAQoA\nPhYhBMHPbjHmut6IaLFytPQu1vurF8ZUBQJc7yaWAhsDBQkDwmcABQsJCAcCBhUK\nCQgLAgQWAgMBAh4BAheAAAoJEPQu1vurF8ZUkhIP/RbZY1ErvCEUy8iLJm9aSpLQ\nnDZl5xILOxyZlzpg+Ml5bb0EkQDr92foCgcvLeANKARNCaGLyNIWkuyDovPV0xZJ\nrEy0kgBrDNb3++NmdI/+GA92pkedMXXioQvqdsxUagXAIB/sNGByJEhs37F05AnF\nvZbjUhceq3xTlvAMcrBWrgB4NwBivZY6IgLvl/CRQpVYwANShIQdbvHvZSxRonWh\nNXr6v/Wcf8rsp7g2VqJ2N2AcWT84aa9BLQ3Oe/SgrNx4QEhA1y7rc3oaqPVu5ZXO\nK+4O14JrpbEZ3Xs9YEjrcOuEDEpYktA8qqUDTdFyZrxb9S6BquUKrA6jZgT913kj\nJ4e7YAZobC4rH0w4u0PrqDgYOkXA9Mo7L601/7ZaDJob80UcK+Z12ZSw73IgBix6\nDiJVfXuWkk5PM2zsFn6UOQXUNlZlDAOj5NC01V0fJ8P0v6GO9YOSSQx0j5UtkUbR\nfp/4W7uCPFvwAatWEHJhlM3sQNiMNStJFegr56xQu1a/cbJH7GdbseMhG/f0BaKQ\nqXCI3ffB5y5AOLc9Hw7PYiTFQsuY1ePRhE+J9mejgWRZxkjAH/FlAubqXkDgterC\nh+sLkzGf+my2IbsMCuc+3aeNMJ5Ej/vlXefCH/MpPWAHCqpQhe2DET/jRSaM53US\nAHNx8kw4MPUkxExgI7Sd\n=4Ofr\n-----END PGP PUBLIC KEY BLOCK-----" > $WORKSPACE/keys/0.key',
        'echo "# END SECTION"',
    ]),
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
        ' --distribution-repository-urls http://repositories.ros.org/ubuntu/main' +
        ' --distribution-repository-key-files $WORKSPACE/keys/0.key' +
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
