#!/usr/bin/env sh
@{
import os
}@

# fail script if any single command fails
set -e

echo "Source job: @source_job_name"
echo "Binary job: @binary_job_name"

BASEPATH=`pwd`
echo "Using BASEPATH: $BASEPATH"

@(TEMPLATE(
    'devel/devel_script_check.sh.em',
))@

WORKSPACE=$BASEPATH/source
echo ""
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:start:source-build-workspace"
@[end if]@
echo "Using workspace for source: $WORKSPACE"

mkdir -p $WORKSPACE
cd $WORKSPACE

# run all source build steps
@(TEMPLATE(
    'devel/devel_script_build.sh.em',
    scripts=source_scripts,
))@
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:end:source-build-workspace"
@[end if]@

WORKSPACE=$BASEPATH/binary
echo ""
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:start:binary-build-workspace"
@[end if]@
echo "Using workspace for binary: $WORKSPACE"

mkdir -p $WORKSPACE
cd $WORKSPACE

echo ""
echo "Get artifacts from source job"
mkdir -p $WORKSPACE/binarydeb
(set -x; cp $BASEPATH/source/sourcedeb/*.debian.tar.[gx]z $BASEPATH/source/sourcedeb/*.dsc $BASEPATH/source/sourcedeb/*.orig.tar.gz $WORKSPACE/binarydeb/)

@(TEMPLATE(
    'devel/devel_script_build.sh.em',
    scripts=binary_scripts,
))@
@[if os.environ.get('TRAVIS') == 'true']@
echo "travis_fold:end:binary-build-workspace"
@[end if]@
