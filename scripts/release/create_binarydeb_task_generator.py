#!/usr/bin/env python3

# Copyright 2014-2016 Open Source Robotics Foundation, Inc.
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
import os
import sys

from apt import Cache
from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_binarypkg_dir
from ros_buildfarm.argument import \
    add_argument_distribution_repository_key_files
from ros_buildfarm.argument import add_argument_distribution_repository_urls
from ros_buildfarm.argument import add_argument_dockerfile_dir
from ros_buildfarm.argument import add_argument_env_vars
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_package_name
from ros_buildfarm.argument import add_argument_rosdistro_index_url
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.common import get_binary_package_versions
from ros_buildfarm.common import get_distribution_repository_keys
from ros_buildfarm.common import get_os_package_name
from ros_buildfarm.common import get_user_id
from ros_buildfarm.templates import create_dockerfile
from rosdistro import get_distribution_file
from rosdistro import get_index


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate a 'Dockerfile' for building the binarydeb")
    add_argument_rosdistro_index_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_package_name(parser)
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)
    add_argument_distribution_repository_urls(parser)
    add_argument_distribution_repository_key_files(parser)
    add_argument_binarypkg_dir(parser)
    add_argument_dockerfile_dir(parser)
    add_argument_env_vars(parser)
    args = parser.parse_args(argv)

    debian_package_name = get_os_package_name(
        args.rosdistro_name, args.package_name)

    # get expected package version from rosdistro
    index = get_index(args.rosdistro_index_url)
    dist_file = get_distribution_file(index, args.rosdistro_name)
    assert args.package_name in dist_file.release_packages
    pkg = dist_file.release_packages[args.package_name]
    repo = dist_file.repositories[pkg.repository_name]
    package_version = repo.release_repository.version

    debian_package_version = package_version

    # build_binarydeb dependencies
    debian_pkg_names = ['apt-src']

    # add build dependencies from .dsc file
    dsc_file = get_dsc_file(
        args.binarypkg_dir, debian_package_name, debian_package_version)
    debian_pkg_names += sorted(get_build_depends(dsc_file))

    # get versions for build dependencies
    apt_cache = Cache()
    debian_pkg_versions = get_binary_package_versions(
        apt_cache, debian_pkg_names)

    # generate Dockerfile
    data = {
        'os_name': args.os_name,
        'os_code_name': args.os_code_name,
        'arch': args.arch,

        'uid': get_user_id(),

        'distribution_repository_urls': args.distribution_repository_urls,
        'distribution_repository_keys': get_distribution_repository_keys(
            args.distribution_repository_urls,
            args.distribution_repository_key_files),

        'build_environment_variables': ['%s=%s' % key_value for key_value in args.env_vars.items()],

        'dependencies': debian_pkg_names,
        'dependency_versions': debian_pkg_versions,
        'install_lists': [],

        'rosdistro_name': args.rosdistro_name,
        'package_name': args.package_name,
        'binarypkg_dir': args.binarypkg_dir,
    }
    create_dockerfile(
        'release/deb/binarypkg_task.Dockerfile.em', data, args.dockerfile_dir)

    # output hints about necessary volumes to mount
    ros_buildfarm_basepath = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..'))
    print('Mount the following volumes when running the container:')
    print('  -v %s:/tmp/ros_buildfarm:ro' % ros_buildfarm_basepath)
    print('  -v %s:/tmp/binarydeb' % args.binarypkg_dir)


def get_dsc_file(basepath, debian_package_name, debian_package_version):
    print("Looking for the '.dsc' file of package '%s' with version '%s'" %
          (debian_package_name, debian_package_version))
    any_dsc_files = []
    dsc_files = []
    for filename in os.listdir(basepath):
        if filename.endswith('.dsc'):
            any_dsc_files.append(filename)
            if filename.startswith(
                    '%s_%s' % (debian_package_name, debian_package_version)):
                dsc_files.append(os.path.join(basepath, filename))
    if not dsc_files:
        print("Could not find the right '.dsc' file", file=sys.stderr)
        if any_dsc_files:
            print("The following '.dsc' files did not match:", file=sys.stderr)
            for any_dsc_file in any_dsc_files:
                print(' - %s' % any_dsc_file, file=sys.stderr)

    assert len(dsc_files) == 1, \
        'The binarydeb job could not find the .dsc file. ' \
        'If a new version of the package has been released recently (within 15 minutes) ' \
        'the new sourcedeb might not have been generated yet and ' \
        'the next automatically scheduled build should succeed.'
    return dsc_files[0]


def get_build_depends(dsc_file):
    with open(dsc_file, 'r') as h:
        content = h.read()

    deps = None
    for line in content.splitlines():
        if line.startswith('Build-Depends: '):
            deps = set([])
            deps_str = line[15:]
            for dep_str in deps_str.split(', '):
                if dep_str.endswith(')'):
                    dep_str = dep_str[:dep_str.find(' (')]
                deps.add(dep_str)
            break
    assert deps is not None
    return deps


if __name__ == '__main__':
    main()
