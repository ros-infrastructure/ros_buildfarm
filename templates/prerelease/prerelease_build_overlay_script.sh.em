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

echo ""
echo "Test results of overlay workspace"
echo ""

@(TEMPLATE(
    'devel/devel_script_test_results.sh.em',
    workspace_path='catkin_workspace_overlay',
))@
