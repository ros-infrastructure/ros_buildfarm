set +e
_ls_prerelease_scripts=`ls | grep -v "prerelease.*\.sh"`
set -e
if [ "$_ls_prerelease_scripts" != "" ]; then
  echo "This script should be executed either in an empty folder or in a folder only containing the prerelease scripts" 1>&2
  if [ "$1" != "-y" ]; then
    read -p "Do you wish to continue anyway, this might overwrite existing files and folders? (y/N) " answer
    case $answer in
      [yY]* ) ;;
      * ) exit 1;;
    esac
  fi
  echo ""
fi
