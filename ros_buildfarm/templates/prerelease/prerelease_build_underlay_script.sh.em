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
    build_tool=build_tool,
    workspace_path='ws',
))@
test_result_RC_underlay=$test_result_RC
unset test_result_RC
if [ -n "$ABORT_ON_TEST_FAILURE_UNDERLAY" -a \
  "$ABORT_ON_TEST_FAILURE_UNDERLAY" != "0" ]
then
  (exit $test_result_RC_underlay)
fi
