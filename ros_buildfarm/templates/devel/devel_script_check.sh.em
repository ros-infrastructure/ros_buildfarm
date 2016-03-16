if [ "`ls`" != "" -a "`ls`" != "`basename $0`" ]; then
  echo "This script should be executed either in an empty folder or in a folder only containing the script itself" 1>&2
  if [ "$1" != "-y" ]; then
    read -p "Do you wish to continue anyway, this might overwrite existing files and folders? (y/N) " answer
    case $answer in
      [yY]* ) ;;
      * ) exit 1;;
    esac
  fi
  echo ""
fi
