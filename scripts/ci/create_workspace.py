#!/usr/bin/env python3

# Copyright 2018 Open Source Robotics Foundation, Inc.
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

import argparse
import os
import sys

def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Create a colcon workspace from vcs repos files.")
    parser.add_argument(
        '--workspace-root',
        help='The path of the desired workspace',
        required=True)
    parser.add_argument(
        '--repos-file-urls',
        help='URLs of repos files to import with vcs.',
        nargs='*',
        required=True)
    args = parser.parse_args(argv)

    if not os.path.isdir(args.workspace_root):
        # TODO(nuclearsandwich) proper error out
        print('no workspace')
        sys.exit(1)
    # get all repos files a la https://github.com/ros2/ci/pull/66/files#diff-dcc9b88c6bfa21d6151296e463494a16R395
    # vcs import each of them
    # Run vcs export --exact to get exact commit ids.


if __name__ == '__main__':
    sys.exit(main())


