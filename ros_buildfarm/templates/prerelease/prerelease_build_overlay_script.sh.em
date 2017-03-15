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
    scripts=overlay_scripts,
))@

if [ -d "$WORKSPACE/catkin_workspace_overlay/test_results" ]; then
    echo ""
    echo "Test results of overlay workspace"
    echo ""

    @(TEMPLATE(
        'devel/devel_script_test_results.sh.em',
        workspace_path='catkin_workspace_overlay',
    ))@
    catkin_test_results_RC_overlay=$catkin_test_results_RC
    unset catkin_test_results_RC
    if [ -n "$ABORT_ON_TEST_FAILURE_OVERLAY" -a \
      "$ABORT_ON_TEST_FAILURE_OVERLAY" != "0" ]
    then
      (exit $catkin_test_results_RC_overlay)
    fi
else
    echo ""
    echo "No test results in overlay workspace"
    echo ""
    catkin_test_results_RC_overlay=0
fi
