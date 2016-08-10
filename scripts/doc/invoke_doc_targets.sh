#!/usr/bin/env sh

# Copyright 2015 Open Source Robotics Foundation, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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
