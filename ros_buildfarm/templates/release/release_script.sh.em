#!/usr/bin/env sh

# fail script if any single command fails
set -e

echo "Source job: @source_job_name"
echo "Binary job: @binary_job_name"

BASEPATH=`pwd`
echo "Using BASEPATH: $BASEPATH"

if [ "`ls`" != "" -a "`ls`" != "`basename $0`" ]; then
  echo "This script should be executed either in an empty folder or in a folder only containing the script itself" 1>&2
  if [ "$1" != "-y" ]; then
    read -p "Do you wish to continue anyway, this might overwrite existing files and folders? (y/N) " answer
    case $answer in
      [yY]* ) ;;
      * ) exit 1;;
    esac
  fi
fi

WORKSPACE=$BASEPATH/source
echo ""
echo "Using workspace for source: $WORKSPACE"

mkdir -p $WORKSPACE
cd $WORKSPACE

# run all source build steps
@[for i, script in enumerate(source_scripts)]@
echo ""
echo "Build step @(i + 1)"
# output the commands executed in this block
(set -x; @script)

@[end for]@

WORKSPACE=$BASEPATH/binary
echo ""
echo "Using workspace for binary: $WORKSPACE"

mkdir -p $WORKSPACE
cd $WORKSPACE

echo ""
echo "Get artifacts from source job"
mkdir -p $WORKSPACE/binarydeb
(set -x; cp $BASEPATH/source/sourcedeb/*.debian.tar.[gx]z $BASEPATH/source/sourcedeb/*.dsc $BASEPATH/source/sourcedeb/*.orig.tar.gz $WORKSPACE/binarydeb/)

# run all binary build steps
@[for i, script in enumerate(binary_scripts)]@
echo ""
echo "Build step @(i + 1)"
# output the commands executed in this block
(set -x; @script)

@[end for]@
