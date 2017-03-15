#!/usr/bin/env sh

# fail script if any single command fails
set -e

if [ -z "$WORKSPACE" ]; then
    WORKSPACE=`pwd`
    echo "Using workspace: $WORKSPACE"
    echo ""
fi

@(TEMPLATE(
    'devel/devel_script_build.sh.em',
    scripts=scripts,
))@

echo ""
echo "Test results of underlay workspace"
echo ""

@(TEMPLATE(
    'devel/devel_script_test_results.sh.em',
    workspace_path='catkin_workspace',
))@
catkin_test_results_RC_underlay=$catkin_test_results_RC
unset catkin_test_results_RC
if [ -n "$ABORT_ON_TEST_FAILURE_UNDERLAY" -a \
  "$ABORT_ON_TEST_FAILURE_UNDERLAY" != "0" ]
then
  (exit $catkin_test_results_RC_underlay)
fi
