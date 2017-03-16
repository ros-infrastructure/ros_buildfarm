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

import sys

from catkin_pkg.package import parse_package_string


def add_overlay_arguments(parser):
    group = parser.add_argument_group(
        'Packages in overlay workspace',
        description='The packages in the overlay workspace will be ' +
                    'built and tested. The workspace will be extended with ' +
                    'packages from GBP repositories for dependencies ' +
                    'between the overlay and underlay workspaces. All other ' +
                    'dependencies will be provided by binary packages.')
    group.add_argument(
        '--pkg',
        nargs='*',
        default=[],
        metavar='PACKAGE_NAME',
        help="A name of a released 'package' from the distribution file to " +
             "be included in the overlay workspace")
    group.add_argument(
        '--exclude-pkg',
        nargs='*',
        default=[],
        metavar='PACKAGE_NAME',
        help="A name of a released 'package' from the distribution file " +
             "which should be excluded from the overlay workspace")
    group.add_argument(
        '--level',
        type=int,
        default=0,
        metavar='DEPENDENCY_LEVEL',
        help="The depth of the depends-on tree to be included in the " +
             "overlay workspace (-1 implies unlimited, default: 0)")


def get_overlay_package_names(
        included_package_names, excluded_package_names, level,
        underlay_package_names, pkg_xmls, output=False):
    # parse all package xmls
    pkgs = {}
    for pkg_name in sorted(pkg_xmls.keys()):
        try:
            pkg = parse_package_string(pkg_xmls[pkg_name])
        except Exception:
            # TODO decide which errors to catch and what to do
            raise
        pkgs[pkg_name] = pkg

    assert set(included_package_names).issubset(set(pkgs.keys()))

    # extract all first-level dependencies (except doc)
    dependencies = {}
    for pkg_name, pkg in pkgs.items():
        all_depends = \
            pkg.build_depends + pkg.buildtool_depends + \
            pkg.build_export_depends + pkg.buildtool_export_depends + \
            pkg.exec_depends + pkg.test_depends
        dependencies[pkg_name] = \
            set([d.name for d in all_depends]) & set(pkgs.keys())

    # determine first-level reverse dependencies
    reverse_dependencies = {}
    for pkg_name in dependencies.keys():
        reverse_dependencies[pkg_name] = set([])
    for pkg_name, dep_names in dependencies.items():
        for dep_name in dep_names:
            reverse_dependencies[dep_name].add(pkg_name)

    # collect overlay package names based on underlay package names and level
    overlay_package_names_from_level = set([])
    if level < 0:
        level = len(pkgs) - 1
    next_level_pkg_names = underlay_package_names
    for _ in range(level):
        next_level_pkg_names = get_next_level_of_dependencies(
            next_level_pkg_names, reverse_dependencies,
            overlay_package_names_from_level | set(underlay_package_names) |
            set(excluded_package_names))
        if not next_level_pkg_names:
            break
        overlay_package_names_from_level |= next_level_pkg_names
    print("Overlay packages based on dependency level: %d" %
          len(overlay_package_names_from_level), file=sys.stderr)

    # collect recursive dependencies of included pkg names
    recursive_included_package_names = set(included_package_names)
    next_level_pkg_names = included_package_names
    for _ in range(len(pkgs) - 1):
        next_level_pkg_names = get_next_level_of_dependencies(
            next_level_pkg_names, dependencies,
            recursive_included_package_names | set(included_package_names))
        if not next_level_pkg_names:
            break
        recursive_included_package_names |= next_level_pkg_names

    # collect recursive reverse dependencies of underlay pkg names
    recursive_underlay_package_names = set([])
    next_level_pkg_names = underlay_package_names
    for _ in range(len(pkgs) - 1):
        next_level_pkg_names = get_next_level_of_dependencies(
            next_level_pkg_names, reverse_dependencies,
            recursive_underlay_package_names | set(underlay_package_names))
        if not next_level_pkg_names:
            break
        recursive_underlay_package_names |= next_level_pkg_names

    # the packages between the included package names and the underlay
    overlay_package_names_from_included_package_names = \
        recursive_included_package_names & recursive_underlay_package_names
    print("Overlay packages based on whitelisted package names: %d" %
          len(overlay_package_names_from_included_package_names),
          file=sys.stderr)

    return overlay_package_names_from_level | \
        overlay_package_names_from_included_package_names


def get_next_level_of_dependencies(names, dependencies, excludes):
    next_level = set([])
    for name in names:
        if name not in dependencies:
            continue
        next_level |= (dependencies[name] - excludes)
    return next_level
