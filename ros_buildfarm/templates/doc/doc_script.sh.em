#!/usr/bin/env sh

# fail script if any single command fails
set -e

echo "Doc job: @doc_job_name"
echo ""

export WORKSPACE=`pwd`
echo "Use workspace: $WORKSPACE"
echo ""

@(TEMPLATE(
    'devel/devel_script_check.sh.em',
))@

echo ""
echo "Clone source repositories"
echo ""

@(TEMPLATE(
    'devel/devel_script_clone.sh.em',
    workspace_path='catkin_workspace',
    scms=scms,
))@

echo ""
echo "Build workspace"
echo ""

@(TEMPLATE(
    'devel/devel_script_build.sh.em',
    scripts=scripts,
))@

echo ""
echo "Generated documentation: $WORKSPACE/generated_documentation/api_rosdoc"
echo ""
