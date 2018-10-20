#!/usr/bin/env sh

# fail script if any single command fails
set -e

if [ -z "$WORKSPACE" ]; then
    WORKSPACE=`pwd`
    echo "Using workspace: $WORKSPACE"
    echo ""
fi

@(TEMPLATE(
    'devel/devel_script_clone.sh.em',
    workspace_path='ws_overlay',
    scms=scms,
))@
