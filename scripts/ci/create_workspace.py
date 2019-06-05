#!/usr/bin/env python3

# Copyright 2019 Open Source Robotics Foundation, Inc.
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
from urllib.request import urlretrieve

from ros_buildfarm.argument import add_argument_repos_file_urls
from ros_buildfarm.argument import add_argument_test_branch
from ros_buildfarm.common import Scope
from ros_buildfarm.vcs import export_repositories, import_repositories
from ros_buildfarm.workspace import ensure_workspace_exists


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Create a workspace from vcs repos files.')
    add_argument_repos_file_urls(parser, required=True)
    add_argument_test_branch(parser)
    parser.add_argument(
        '--workspace-root',
        help='The path of the desired workspace',
        required=True)
    args = parser.parse_args(argv)

    ensure_workspace_exists(args.workspace_root)

    with Scope('SUBSECTION', 'fetch repos files(s)'):
        repos_files = []
        for repos_file_url in args.repos_file_urls:
            repos_file = os.path.join(args.workspace_root, os.path.basename(repos_file_url))
            print('Fetching \'%s\' to \'%s\'' % (repos_file_url, repos_file))
            urlretrieve(repos_file_url, repos_file)
            repos_files += [repos_file]

    with Scope('SUBSECTION', 'import repositories'):
        source_space = os.path.join(args.workspace_root, 'src')
        for repos_file in repos_files:
            print('Importing repositories from \'%s\'' % (repos_file))
            import_repositories(source_space, repos_file, args.test_branch)

    with Scope('SUBSECTION', 'vcs export --exact'):
        export_repositories(args.workspace_root)


if __name__ == '__main__':
    sys.exit(main())
