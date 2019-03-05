#!/usr/bin/env sh
@{
import os
}@

# fail script if any single command fails
set -e

echo "CI job: @ci_job_name"
echo ""
echo "By default this script will not return an error code if any tests fail."
echo "If you want the script to return a non-zero return code in that case"
echo "you can set the environment variable ABORT_ON_TEST_FAILURE=1."
echo ""

export WORKSPACE=`pwd`
echo "Use workspace: $WORKSPACE"
echo ""

@(TEMPLATE(
    'devel/devel_script_check.sh.em',
))@

@(TEMPLATE(
    'ci/ci_script_set_parameters.sh.em',
    parameters=parameters,
))@

echo ""
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:start:ci-clone-and-build"
@[end if]@
echo "Clone Repositories and Build workspace"
echo ""

@(TEMPLATE(
    'devel/devel_script_build.sh.em',
    scripts=scripts,
))@
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:end:ci-clone-and-build"
@[end if]@

echo ""
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:start:ci-test-results"
@[end if]@
echo "Test results"
echo ""

@(TEMPLATE(
    'devel/devel_script_test_results.sh.em',
    build_tool=build_tool,
    workspace_path='ws',
))@
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:end:ci-test-results"
@[end if]@
