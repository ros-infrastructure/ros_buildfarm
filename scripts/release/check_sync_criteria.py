#!/usr/bin/env python3

# Copyright 2014-2015 Open Source Robotics Foundation, Inc.
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

from __future__ import print_function

import argparse
import sys

from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_cache_dir
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_return_zero
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.common import get_os_package_name
from ros_buildfarm.common import Target
from ros_buildfarm.config import get_index as get_config_index
from ros_buildfarm.config import get_release_build_files
from ros_buildfarm.package_repo import get_package_repo_data
from rosdistro import get_distribution_file
from rosdistro import get_index


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Check if the sync criteria are matched to sync ' +
                    'packages from the building to the testing repo')
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'release')
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)
    add_argument_cache_dir(parser, '/tmp/package_repo_cache')
    add_argument_return_zero(parser)
    args = parser.parse_args(argv)

    success = check_sync_criteria(
        args.config_url, args.rosdistro_name, args.release_build_name,
        args.os_name, args.os_code_name, args.arch, args.cache_dir)
    return 0 if success or args.return_zero else 1


def check_sync_criteria(
        config_url, rosdistro_name, release_build_name, os_name,
        os_code_name, arch, cache_dir):
    # fetch debian package list
    config = get_config_index(config_url)
    index = get_index(config.rosdistro_index_url)
    dist_file = get_distribution_file(index, rosdistro_name)
    build_files = get_release_build_files(config, rosdistro_name)
    build_file = build_files[release_build_name]

    target = Target(os_name, os_code_name, arch)

    repo_index = get_package_repo_data(
        build_file.target_repository, [target], cache_dir)[target]

    # for each release package which matches the release build file
    # check if a binary package exists
    binary_packages = {}
    all_pkg_names = dist_file.release_packages.keys()
    pkg_names = build_file.filter_packages(all_pkg_names)
    for pkg_name in sorted(pkg_names):
        debian_pkg_name = get_os_package_name(rosdistro_name, pkg_name)
        binary_packages[pkg_name] = debian_pkg_name in repo_index

    # check that all elements from whitelist are present
    if build_file.sync_packages:
        missing_binary_packages = [
            pkg_name
            for pkg_name in build_file.sync_packages
            if pkg_name not in binary_packages or not binary_packages[pkg_name]]
        if missing_binary_packages:
            print('The following binary packages are missing to sync:',
                  file=sys.stderr)
            for pkg_name in sorted(missing_binary_packages):
                print('-', pkg_name, file=sys.stderr)
            return False
        print('All required binary packages are available:')
        for pkg_name in sorted(build_file.sync_packages):
            print('-', pkg_name)

    # check that count is satisfied
    if build_file.sync_package_count is not None:
        binary_package_count = len([
            pkg_name
            for pkg_name, has_binary_package in binary_packages.items()
            if has_binary_package])
        if binary_package_count < build_file.sync_package_count:
            print('Only %d binary packages available ' % binary_package_count +
                  '(at least %d are required to sync)' %
                  build_file.sync_package_count, file=sys.stderr)
            return False
        print('%d binary packages available ' % binary_package_count +
              '(more or equal then the configured sync limit of %d)' %
              build_file.sync_package_count)

    return True


if __name__ == '__main__':
    sys.exit(main())
