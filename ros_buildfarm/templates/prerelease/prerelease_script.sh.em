#!/usr/bin/env sh
@{
import os
}@

# fail script if any single command fails
set -e

echo "Prerelease script"
echo ""
echo "By default this script will continue even if tests fail."
echo "If you want the script to abort and return a non-zero return code"
echo "you can set the environment variable ABORT_ON_TEST_FAILURE=1."
echo "You can also set ABORT_ON_TEST_FAILURE_UNDERLAY=1 or"
echo "ABORT_ON_TEST_FAILURE_OVERLAY=1 to only affect a specific workspace."
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
. `pwd`/prerelease_build_underlay.sh
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:end:prerelease-build-underlay-workspace"
@[end if]@
echo ""

echo ""
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:start:prerelease-build-overlay-workspace"
@[end if]@
if [ "$(ls -A "$WORKSPACE/ws_overlay/src" 2> /dev/null)" != "" ]; then
  echo "Build overlay workspace"
  echo ""
  . `pwd`/prerelease_build_overlay.sh
else
  echo "Skipping empty overlay workspace"
fi
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:end:prerelease-build-overlay-workspace"
@[end if]@
echo ""
