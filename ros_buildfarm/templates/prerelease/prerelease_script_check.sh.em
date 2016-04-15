set +e
_ls_prerelease_scripts=`ls | grep -v "prerelease.*\.sh"`
set -e
if [ "$_ls_prerelease_scripts" != "" ]; then
  echo "Files from previous prerelease tests are found. These files help speeding things up if you mean to repeat the test for the same repository. If you're testing different repository than the one in previous test, you need to remove them as this script should be executed either in an empty folder or in a folder only containing the prerelease scripts" 1>&2
  if [ "$1" != "-y" ]; then
    read -p "Do you wish to continue anyway, this might overwrite existing files and folders? (y/N) " answer
    case $answer in
      [yY]* ) ;;
      * ) echo "Exiting. If you're testing difrrent repo, you might want to remove the following folders: ${_ls_prerelease_scripts}." && exit 1;;
    esac
  fi
  echo ""
fi
