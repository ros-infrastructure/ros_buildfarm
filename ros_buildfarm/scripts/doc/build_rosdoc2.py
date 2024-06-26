# Copyright 2015-2016 Open Source Robotics Foundation, Inc.
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
import subprocess
import sys

from catkin_pkg.packages import find_packages
from ros_buildfarm.common import Scope
from ros_buildfarm.workspace import clean_workspace
from ros_buildfarm.workspace import ensure_workspace_exists


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Invoke 'rosdoc2' on each package of a workspace")
    parser.add_argument(
        '--workspace-root',
        required=True,
        help='The root path of the workspace to document')
    parser.add_argument(
        '--rosdoc2-dir',
        required=True,
        help='The root path of the rosdoc2 repository')
    parser.add_argument(
        'pkg_tuples',
        nargs='*',
        help='A list of package tuples in topological order, each containing '
             'the name, and the relative path separated by a colon')
    args = parser.parse_args(argv)

    ensure_workspace_exists(args.workspace_root)
    clean_workspace(args.workspace_root)

    with Scope('SUBSECTION', 'Installing rosdoc2'):
        env = {
            **os.environ,
            'PIP_BREAK_SYSTEM_PACKAGES': '1',
        }

        pip_rc = subprocess.call(['python3',
                                  '-m',
                                  'pip',
                                  'install',
                                  '--no-warn-script-location',
                                  '.'],
                                 env=env,
                                 cwd=args.rosdoc2_dir)
        if pip_rc:
            return pip_rc

    with Scope('SUBSECTION', 'rosdoc2'):
        env = {
            **os.environ,
        }
        if 'PATH' not in env:
            env['PATH'] = ''
        else:
            env['PATH'] += ':'
        env['PATH'] += '/home/buildfarm/.local/bin'

        source_space = os.path.join(args.workspace_root, 'src')
        print("Crawling for packages in workspace '%s'" % (source_space))
        pkgs = find_packages(source_space)

        pkg_names = [pkg.name for pkg in pkgs.values()]
        print('Found the following packages:')
        for pkg_name in sorted(pkg_names):
            print('  -', pkg_name)

        for pkg_path, pkg in pkgs.items():
            abs_pkg_path = os.path.join(source_space, pkg_path)
            cmd = ['rosdoc2', 'build', '--package-path', abs_pkg_path]
            subprocess.call(cmd, cwd=args.workspace_root, env=env)

    return 0


if __name__ == '__main__':
    sys.exit(main())
