#!/usr/bin/env sh

# fail script if any single command fails
set -e

if [ -z "$WORKSPACE" ]; then
    WORKSPACE=`pwd`
    echo "Using workspace: $WORKSPACE"
    echo ""
fi

PYTHONPATH=@ros_buildfarm_python_path:$PYTHONPATH @python_executable @prerelease_script_path/generate_prerelease_overlay_script.py @config_url @rosdistro_name @os_name @os_code_name @arch --pkg @(' '.join(pkg)) --exclude-pkg @(' '.join(exclude_pkg)) --level @level --vcstool > overlay.repos
echo ""

vcs import $WORKSPACE < overlay.repos
