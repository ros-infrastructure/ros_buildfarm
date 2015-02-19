#!/usr/bin/env sh

# fail script if any single command fails
set -e

BASE_DIR=$1
OUTPUT_DIR=$2

cd $BASE_DIR
SUBDIRS="`find . -maxdepth 1 -mindepth 1 -type d -exec basename '{}' \;`"
export PYTHONPATH=""

for subdir in $SUBDIRS
do
  export PYTHONPATH=$BASE_DIR/$subdir/src:$PYTHONPATH
done

echo "PYTHONPATH=$PYTHONPATH"

for subdir in $SUBDIRS
do
  echo "# BEGIN SUBSECTION: $subdir: make html"
  cd $BASE_DIR/$subdir/doc
  mkdir -p $OUTPUT_DIR/$subdir
  ln -s $OUTPUT_DIR/$subdir _build
  (set -x; make html)
  echo "# END SUBSECTION"
  echo ""
done
