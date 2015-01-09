#!/usr/bin/env sh

# fail script if any single command fails
set -e

echo "Prerelease script"
echo ""

export WORKSPACE=`pwd`
echo "Use workspace: $WORKSPACE"
echo ""

@(TEMPLATE(
    'prerelease/prerelease_script_check.sh.em',
))@

echo ""
echo "Clone source repositories for underlay workspace"
echo ""
./prerelease_clone_underlay.sh
echo ""

echo ""
echo "Clone release repositories for overlay workspace"
echo ""
./prerelease_clone_overlay.sh
echo ""

echo ""
echo "Build underlay workspace"
echo ""
./prerelease_build_underlay.sh
echo ""

echo ""
echo "Build overlay workspace"
echo ""
./prerelease_build_overlay.sh
echo ""
