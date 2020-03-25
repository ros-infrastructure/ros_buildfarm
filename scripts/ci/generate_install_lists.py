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
from pathlib import Path
import sys

from apt import Cache
from catkin_pkg.packages import find_packages
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_output_dir
from ros_buildfarm.argument import add_argument_package_selection_args
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.argument import add_argument_skip_rosdep_keys
from ros_buildfarm.colcon import locate_packages
from ros_buildfarm.common import get_binary_package_versions
from ros_buildfarm.common import Scope
from rosdep2 import create_default_installer_context
from rosdep2.catkin_support import get_catkin_view
from rosdep2.catkin_support import resolve_for_os


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description='Lists available binary packages and versions which are'
                    'needed to satisfy rosdep keys for ROS packages in the workspace')

    # Positional
    add_argument_rosdistro_name(parser)
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)

    add_argument_output_dir(parser)
    add_argument_package_selection_args(parser)
    add_argument_skip_rosdep_keys(parser)
    parser.add_argument(
        '--package-root',
        nargs='+',
        help='The path to the directory containing packages')
    args = parser.parse_args(argv)

    workspace_root = args.package_root[-1]
    os.chdir(workspace_root)

    with Scope('SUBSECTION', 'mark packages with IGNORE files'):
        all_packages = locate_packages(workspace_root)
        selected_packages = all_packages
        if args.package_selection_args:
            print(
                'Using package selection arguments:',
                args.package_selection_args)
            selected_packages = locate_packages(
                workspace_root, extra_args=args.package_selection_args)

            to_ignore = all_packages.keys() - selected_packages.keys()
            print('Ignoring %d packages' % len(to_ignore))
            for package in sorted(to_ignore):
                print('-', package)
                package_root = all_packages[package]
                Path(package_root, 'COLCON_IGNORE').touch()

        print('There are %d packages which meet selection criteria' %
              len(selected_packages))

    with Scope('SUBSECTION', 'Enumerating packages needed to build'):
        # find all of the underlay packages
        underlay_pkgs = {}
        all_underlay_pkg_names = set()
        for package_root in args.package_root[0:-1]:
            print("Crawling for packages in '%s'" % package_root)
            underlay_pkgs.update(find_packages(package_root))

            # Check for a colcon index for non-ROS package detection
            colcon_index = os.path.join(package_root, 'colcon-core', 'packages')
            try:
                all_underlay_pkg_names.update(os.listdir(colcon_index))
            except FileNotFoundError:
                pass

        underlay_pkg_names = [pkg.name for pkg in underlay_pkgs.values()]
        print('Found the following ROS underlay packages:')
        for pkg_name in sorted(underlay_pkg_names):
            print('  -', pkg_name)

        # get direct build dependencies
        package_root = args.package_root[-1]
        print("Crawling for packages in '%s'" % package_root)
        pkgs = find_packages(package_root)

        pkg_names = [pkg.name for pkg in pkgs.values()]
        print('Found the following ROS packages:')
        for pkg_name in sorted(pkg_names):
            print('  -', pkg_name)

        # get build dependencies and map them to binary packages
        all_pkgs = set(pkgs.values()).union(underlay_pkgs.values())

        for pkg in all_pkgs:
            pkg.evaluate_conditions(os.environ)
        for pkg in all_pkgs:
            for group_depend in pkg.group_depends:
                if group_depend.evaluated_condition is not False:
                    group_depend.extract_group_members(all_pkgs)

        dependency_keys_build = get_dependencies(
            all_pkgs, 'build', _get_build_and_recursive_run_dependencies,
            pkgs.values())

        dependency_keys_test = get_dependencies(
            all_pkgs, 'run and test', _get_test_and_recursive_run_dependencies,
            pkgs.values())

        if args.skip_rosdep_keys:
            dependency_keys_build.difference_update(args.skip_rosdep_keys)
            dependency_keys_test.difference_update(args.skip_rosdep_keys)

        # remove all non-ROS packages and packages which are present but
        # specifically ignored
        every_package_name = all_packages.keys() | all_underlay_pkg_names
        dependency_keys_build -= every_package_name
        dependency_keys_test -= every_package_name

        context = initialize_resolver(
            args.rosdistro_name, args.os_name, args.os_code_name)

        os_pkg_names_build = resolve_names(dependency_keys_build, **context)
        os_pkg_names_test = resolve_names(dependency_keys_test, **context)

        os_pkg_names_test -= os_pkg_names_build

    with Scope('SUBSECTION', 'Resolving packages versions using apt cache'):
        apt_cache = Cache()
        os_pkg_versions = get_binary_package_versions(
            apt_cache, os_pkg_names_build | os_pkg_names_test)

    with open(os.path.join(args.output_dir, 'install_list_build.txt'), 'w') as out_file:
        for package in sorted(os_pkg_names_build):
            out_file.write('# break docker cache %s=%s\n' % (package, os_pkg_versions[package]))
            out_file.write('%s\n' % (package))

    with open(os.path.join(args.output_dir, 'install_list_test.txt'), 'w') as out_file:
        for package in sorted(os_pkg_names_test):
            out_file.write('# break docker cache %s=%s\n' % (package, os_pkg_versions[package]))
            out_file.write('%s\n' % (package))


def get_dependencies(pkgs, label, get_dependencies_callback, target_pkgs):
    pkg_names = [pkg.name for pkg in pkgs]
    depend_names = set([])
    for pkg in target_pkgs:
        depend_names.update(
            [d for d in get_dependencies_callback(pkg, pkgs)
             if d not in pkg_names])
    print('Identified the following %s dependencies ' % label +
          '(ignoring packages available from source):')
    for depend_name in sorted(depend_names):
        print('  -', depend_name)
    return depend_names


def _get_build_and_recursive_run_dependencies(pkg, pkgs):
    depends = [
        d.name for d in pkg.build_depends + pkg.buildtool_depends
        if d.evaluated_condition is not False]
    # include recursive run dependencies on other pkgs in the workspace
    # if pkg A in the workspace build depends on pkg B in the workspace
    # then the recursive run dependencies of pkg B need to be installed
    # in order to build the workspace
    other_pkgs_by_names = \
        dict([(p.name, p) for p in pkgs if p.name != pkg.name])
    run_depends_in_pkgs = \
        set([d for d in depends if d in other_pkgs_by_names])
    while run_depends_in_pkgs:
        # pick first element from sorted order to ensure deterministic results
        pkg_name = sorted(run_depends_in_pkgs).pop(0)
        pkg = other_pkgs_by_names[pkg_name]
        other_pkgs_by_names.pop(pkg_name)
        run_depends_in_pkgs.remove(pkg_name)

        # append run dependencies
        run_depends = [
            d.name for d in pkg.build_export_depends +
            pkg.buildtool_export_depends + pkg.exec_depends
            if d.evaluated_condition is not False]

        # append group dependencies
        run_depends += [
            member for group in pkg.group_depends for member in group.members
            if group.evaluated_condition is not False]

        depends += run_depends

        # consider recursive dependencies
        run_depends_in_pkgs.update(
            [d for d in run_depends if d in other_pkgs_by_names])

    return depends


def _get_test_and_recursive_run_dependencies(pkg, pkgs):
    depends = [
        d.name for d in pkg.build_export_depends +
        pkg.buildtool_export_depends + pkg.exec_depends + pkg.test_depends
        if d.evaluated_condition is not False]
    # include recursive run dependencies on other pkgs in the workspace
    # if pkg A in the workspace test depends on pkg B in the workspace
    # then the recursive run dependencies of pkg B need to be installed
    # in order to test the workspace
    other_pkgs_by_names = \
        dict([(p.name, p) for p in pkgs if p.name != pkg.name])
    run_depends_in_pkgs = \
        set([d for d in depends if d in other_pkgs_by_names])
    while run_depends_in_pkgs:
        # pick first element from sorted order to ensure deterministic results
        pkg_name = sorted(run_depends_in_pkgs).pop(0)
        pkg = other_pkgs_by_names[pkg_name]
        other_pkgs_by_names.pop(pkg_name)
        run_depends_in_pkgs.remove(pkg_name)

        # append run dependencies
        run_depends = [
            d.name for d in pkg.build_export_depends +
            pkg.buildtool_export_depends + pkg.exec_depends
            if d.evaluated_condition is not False]

        # append group dependencies
        run_depends += [
            member for group in pkg.group_depends for member in group.members
            if group.evaluated_condition is not False]

        depends += run_depends

        # consider recursive dependencies
        run_depends_in_pkgs.update(
            [d for d in run_depends if d in other_pkgs_by_names])

    return depends


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
