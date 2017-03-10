#!/usr/bin/env sh
@{
import os
}@

# fail script if any single command fails
set -e

echo "Devel job: @devel_job_name"
echo ""

export WORKSPACE=`pwd`
echo "Use workspace: $WORKSPACE"
echo ""

@(TEMPLATE(
    'devel/devel_script_check.sh.em',
))@

echo ""
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:start:devel-clone-source-repos"
@[end if]@
echo "Clone source repositories"
echo ""

@(TEMPLATE(
    'devel/devel_script_clone.sh.em',
    workspace_path='catkin_workspace',
    scms=scms,
))@
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:end:devel-clone-source-repos"
@[end if]@

echo ""
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:start:devel-build-workspace"
@[end if]@
echo "Build workspace"
echo ""

@(TEMPLATE(
    'devel/devel_script_build.sh.em',
    scripts=scripts,
))@
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:end:devel-build-workspace"
@[end if]@

echo ""
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:start:devel-test-results"
@[end if]@
echo "Test results"
echo ""

@(TEMPLATE(
    'devel/devel_script_test_results.sh.em',
    workspace_path='catkin_workspace',
))@
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:end:devel-test-results"
@[end if]@
