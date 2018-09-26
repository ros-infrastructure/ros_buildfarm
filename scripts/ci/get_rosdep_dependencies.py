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

from apt import Cache
from catkin_pkg.packages import find_packages
from ros_buildfarm.common import get_binary_package_versions
from ros_buildfarm.common import Scope
from ros_buildfarm.workspace import ensure_workspace_exists
from rosdep2 import create_default_installer_context
from rosdep2.catkin_support import get_catkin_view
from rosdep2.catkin_support import resolve_for_os


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Lists available binary packages and versions which are"
            "needed to satisfy rosdep keys for ROS packages in the workspace")
    parser.add_argument(
        '--rosdistro-name',
        required=True,
        help='The name of the ROS distro to identify the setup file to be '
             'sourced')
    parser.add_argument(
        '--package-root',
        required=True,
        help='The root directory containing the packages to inspect')
    parser.add_argument(
        '--os-name',
        required=True,
        help="The OS name (e.g. 'ubuntu')")
    parser.add_argument(
        '--os-code-name',
        required=True,
        help="The OS code name (e.g. 'xenial')")
    parser.add_argument(
        '--testing',
        action='store_true',
        help='The flag if the workspace should be built with tests enabled '
             'and instead of installing the tests are ran')
    parser.add_argument(
        '--output-file',
        required=True,
        help="File in which to store the packages and versions")
    parser.add_argument(
        '--skip-rosdep-keys',
        nargs='*',
        help="The specified rosdep keys will be ignored, i.e. not resolved "
             "and not installed.")
    args = parser.parse_args(argv)

    with Scope('SUBSECTION', 'Enumerating packages needed to build'):
        # get direct build dependencies
        print("Crawling for packages in workspace '%s'" % args.package_root)
        pkgs = find_packages(args.package_root)

        pkg_names = [pkg.name for pkg in pkgs.values()]
        print("Found the following packages:")
        for pkg_name in sorted(pkg_names):
            print('  -', pkg_name)

        context = initialize_resolver(
            args.rosdistro_name, args.os_name, args.os_code_name)

        # get build dependencies and map them to binary packages
        dependency_keys = get_dependencies(
            pkgs.values(), 'build', _get_build_and_recursive_run_dependencies)

        if args.testing:
            # get run and test dependencies and map them to binary packages
            dependency_keys += get_dependencies(
                pkgs.values(), 'run and test', _get_run_and_test_dependencies)

        debian_pkg_names = resolve_names(dependency_keys.difference(args.skip_rosdep_keys), **context)

        ## Workarounds for build

        # TODO(cottsay): Deps for fastrtps
        debian_pkg_names.update(['libasio-dev', 'libtinyxml2-dev'])

        ## Workarounds for test

        # TODO(cottsay): Deps for various ament packages
        debian_pkg_names.update(['libxml2-utils', 'python3-flake8', 'python3-pep8', 'python3-pydocstyle'])

        # TODO(cottsay): osrf_pycommon
        debian_pkg_names.update(['python3-mock'])

        # TODO(cottsay): ??
        debian_pkg_names.update(['cppcheck'])


    with Scope('SUBSECTION', 'Resolving packages versions using apt cache'):
        apt_cache = Cache()
        debian_pkg_versions = get_binary_package_versions(
            apt_cache, debian_pkg_names)
        pass

    with open(args.output_file, "w") as out_file:
        for package in sorted(debian_pkg_versions):
            out_file.write("%s=%s\n" % (package, debian_pkg_versions[package]))


def get_dependencies(pkgs, label, get_dependencies_callback):
    pkg_names = [pkg.name for pkg in pkgs]
    depend_names = set([])
    for pkg in pkgs:
        depend_names.update(
            [d.name for d in get_dependencies_callback(pkg, pkgs)
             if d.name not in pkg_names])
    print('Identified the following %s dependencies ' % label +
          '(ignoring packages available from source):')
    for depend_name in sorted(depend_names):
        print('  -', depend_name)
    return depend_names


def _get_build_and_recursive_run_dependencies(pkg, pkgs):
    depends = pkg.build_depends + pkg.buildtool_depends
    # include recursive run dependencies on other pkgs in the workspace
    # if pkg A in the workspace build depends on pkg B in the workspace
    # then the recursive run dependencies of pkg B need to be installed
    # in order to build the workspace
    other_pkgs_by_names = \
        dict([(p.name, p) for p in pkgs if p.name != pkg.name])
    run_depends_in_pkgs = \
        set([d.name for d in depends if d.name in other_pkgs_by_names])
    while run_depends_in_pkgs:
        # pick first element from sorted order to ensure deterministic results
        pkg_name = sorted(run_depends_in_pkgs).pop(0)
        pkg = other_pkgs_by_names[pkg_name]
        other_pkgs_by_names.pop(pkg_name)
        run_depends_in_pkgs.remove(pkg_name)

        # append run dependencies
        run_depends = pkg.build_export_depends + \
            pkg.buildtool_export_depends + pkg.exec_depends
        depends += run_depends

        # consider recursive dependencies
        run_depends_in_pkgs.update(
            [d.name for d in run_depends if d.name in other_pkgs_by_names])

    return depends


def _get_run_and_test_dependencies(pkg, pkgs):
    return pkg.build_export_depends + pkg.buildtool_export_depends + \
        pkg.exec_depends + pkg.test_depends


def initialize_resolver(rosdistro_name, os_name, os_code_name):
    # resolve rosdep keys into binary package names
    ctx = create_default_installer_context()
    try:
        installer_key = ctx.get_default_os_installer_key(os_name)
    except KeyError:
        raise RuntimeError(
            "Could not determine the rosdep installer for '%s'" % os_name)
    installer = ctx.get_installer(installer_key)
    view = get_catkin_view(rosdistro_name, os_name, os_code_name, update=False)
    return {
        'os_name': os_name,
        'os_code_name': os_code_name,
        'installer': installer,
        'view': view,
    }


def resolve_names(rosdep_keys, os_name, os_code_name, view, installer):
    debian_pkg_names = set([])
    for rosdep_key in sorted(rosdep_keys):
        try:
            resolved_names = resolve_for_os(
                rosdep_key, view, installer, os_name, os_code_name)
        except KeyError:
            raise RuntimeError(
                "Could not resolve the rosdep key '%s'" % rosdep_key)
        debian_pkg_names.update(resolved_names)
    print('Resolved the dependencies to the following binary packages:')
    for debian_pkg_name in sorted(debian_pkg_names):
        print('  -', debian_pkg_name)
    return debian_pkg_names


if __name__ == '__main__':
    sys.exit(main())
