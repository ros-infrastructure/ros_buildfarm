#!/usr/bin/env sh

# fail script if any single command fails
set -e

echo "Devel job: @devel_job_name"

WORKSPACE=`pwd`
echo "Using workspace: $WORKSPACE"

if [ "`ls`" != "" -a "`ls`" != "`basename $0`" ]; then
  echo "This script should be executed either in an empty folder or in a folder only containing the script itself" 1>&2
  read -p "Do you wish to continue anyway, this might overwrite existing files and folders? (y/N) " answer
  case $answer in
    [yY]* ) ;;
    * ) exit 1;;
  esac
fi

echo ""
echo "Fetch source repositories"
mkdir -p catkin_workspace/src

@[for i, (repo_spec, path) in enumerate(scms)]@
if [ -d "@path" ]; then
  (set -x; rm -fr @path)
fi
@[if repo_spec.type == 'git']@
(set -x; git clone -b @repo_spec.version @repo_spec.url @path)
@[elif repo_spec.type == 'hg']@
(set -x; hg clone -b @repo_spec.version @repo_spec.url @path)
@[elif repo_spec.type == 'svn']@
(set -x; svn checkout -r @repo_spec.version @repo_spec.url @path)
@[else]@
echo "Unsupported repository type '@repo_spec.type' (@repo_spec.url)"
exit 1
@[end if]@

@[end for]@

# run all build steps
@[for i, script in enumerate(scripts)]@
echo ""
echo "Build step @(i + 1)"
# output the commands executed in this block
(set -x; @script)

@[end for]@

# output test summary
echo ""
echo "Test result"
if type "catkin_test_results" > /dev/null; then
  (set -x; catkin_test_results $WORKSPACE/catkin_workspace/build_isolated --all)
else
  echo "If 'catkin_test_results' would be available it would output a summary of all test results..."
fi
