# Copyright 2025 Open Source Robotics Foundation, Inc.
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
import hashlib
import os
import sys
import tarfile

from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.common import Scope


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Create a compressed archive of the workspace install space.')
    add_argument_rosdistro_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)
    parser.add_argument(
        '--ros-version',
        type=int,
        required=True,
        help='The ROS version (1 or 2)')
    parser.add_argument(
        '--install-dir',
        required=True,
        help='The path to the install space to archive')
    parser.add_argument(
        '--output-dir',
        default='.',
        help='The directory to write the archive and checksum to')
    args = parser.parse_args(argv)

    rosdistro_name = args.rosdistro_name if args.rosdistro_name else 'global'
    archive_name = 'ros%d-%s-linux-%s-%s-ci.tar.bz2' % (
        args.ros_version, rosdistro_name, args.os_code_name, args.arch)
    archive_path = os.path.join(args.output_dir, archive_name)
    checksum_path = archive_path.replace('.tar.bz2', '-CHECKSUM')
    arcname = 'ros%d-linux' % args.ros_version

    with Scope('SUBSECTION', 'create workspace archive'):
        print("Creating archive '%s' from '%s'" % (archive_path, args.install_dir))
        with tarfile.open(archive_path, 'w:bz2') as t:
            t.add(args.install_dir, arcname=arcname)

        print("Computing SHA256 checksum")
        h = hashlib.sha256()
        with open(archive_path, 'rb') as f:
            h.update(f.read())

        checksum_content = '%s *%s\n' % (h.hexdigest(), archive_name)
        print("Writing checksum to '%s'" % checksum_path)
        with open(checksum_path, 'w') as f:
            f.write(checksum_content)

    return 0


if __name__ == '__main__':
    sys.exit(main())
