#!/usr/bin/env sh
@{
import os
}@

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
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:start:prerelease-clone-underlay-repos"
@[end if]@
echo "Clone source repositories for underlay workspace"
echo ""
./prerelease_clone_underlay.sh
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:end:prerelease-clone-underlay-repos"
@[end if]@
echo ""

echo ""
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:start:prerelease-clone-overlay-repos"
@[end if]@
echo "Clone release repositories for overlay workspace"
echo ""
./prerelease_clone_overlay.sh
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:end:prerelease-clone-overlay-repos"
@[end if]@
echo ""

echo ""
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:start:prerelease-build-underlay-workspace"
@[end if]@
echo "Build underlay workspace"
echo ""
. prerelease_build_underlay.sh
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:end:prerelease-build-underlay-workspace"
@[end if]@
echo ""

echo ""
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:start:prerelease-build-overlay-workspace"
@[end if]@
echo "Build overlay workspace"
echo ""
. prerelease_build_overlay.sh
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:end:prerelease-build-overlay-workspace"
@[end if]@
echo ""
