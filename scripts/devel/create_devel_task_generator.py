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

import argparse
import os
import sys

from apt import Cache
from ros_buildfarm.argument import add_argument_build_tool
from ros_buildfarm.argument import add_argument_build_tool_args
from ros_buildfarm.argument import add_argument_build_tool_test_args
from ros_buildfarm.argument import \
    add_argument_distribution_repository_key_files
from ros_buildfarm.argument import add_argument_distribution_repository_urls
from ros_buildfarm.argument import add_argument_dockerfile_dir
from ros_buildfarm.argument import add_argument_env_vars
from ros_buildfarm.argument import add_argument_require_gpu_support
from ros_buildfarm.argument import add_argument_ros_version
from ros_buildfarm.argument import add_argument_run_abichecker
from ros_buildfarm.argument import extract_multiple_remainders
from ros_buildfarm.common import get_binary_package_versions
from ros_buildfarm.common import get_distribution_repository_keys
from ros_buildfarm.common import get_packages_in_workspaces
from ros_buildfarm.common import get_user_id
from ros_buildfarm.templates import create_dockerfile
from rosdep2 import create_default_installer_context
from rosdep2.catkin_support import get_catkin_view
from rosdep2.catkin_support import resolve_for_os


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate a 'Dockerfile' for the devel job")
    parser.add_argument(
        '--rosdistro-name',
        required=True,
        help='The name of the ROS distro to identify the setup file to be '
             'sourced')
    parser.add_argument(
        '--workspace-root',
        nargs='+',
        help='The root path of the workspace to compile')
    parser.add_argument(
        '--os-name',
        required=True,
        help="The OS name (e.g. 'ubuntu')")
    parser.add_argument(
        '--os-code-name',
        required=True,
        help="The OS code name (e.g. 'xenial')")
    parser.add_argument(
        '--arch',
        required=True,
        help="The architecture (e.g. 'amd64')")
    add_argument_distribution_repository_urls(parser)
    add_argument_distribution_repository_key_files(parser)
    add_argument_build_tool(parser, required=True)
    add_argument_ros_version(parser)
    add_argument_env_vars(parser)
    add_argument_dockerfile_dir(parser)
    add_argument_run_abichecker(parser)
    add_argument_require_gpu_support(parser)
    a1 = add_argument_build_tool_args(parser)
    a2 = add_argument_build_tool_test_args(parser)
    parser.add_argument(
        '--testing',
        action='store_true',
        help='The flag if the workspace should be built with tests enabled '
             'and instead of installing the tests are ran')

    remainder_args = extract_multiple_remainders(argv, (a1, a2))
    args = parser.parse_args(argv)
    for k, v in remainder_args.items():
        setattr(args, k, v)

    condition_context = dict(args.env_vars)
    condition_context['ROS_DISTRO'] = args.rosdistro_name
    condition_context['ROS_VERSION'] = args.ros_version

    # get direct build dependencies
    pkgs = get_packages_in_workspaces(args.workspace_root, condition_context)
    pkg_names = [pkg.name for pkg in pkgs.values()]
    print("Found the following packages:")
    for pkg_name in sorted(pkg_names):
        print('  -', pkg_name)

    maintainer_emails = set([])
    for pkg in pkgs.values():
        for m in pkg.maintainers:
            maintainer_emails.add(m.email)
    if maintainer_emails:
        print('Package maintainer emails: %s' %
              ' '.join(sorted(maintainer_emails)))

    context = initialize_resolver(
        args.rosdistro_name, args.os_name, args.os_code_name)

    apt_cache = Cache()

    debian_pkg_names = [
        'build-essential',
        'python3',
    ]
    if args.build_tool == 'colcon':
        debian_pkg_names += [
            'python3-colcon-metadata',
            'python3-colcon-output',
            'python3-colcon-parallel-executor',
            'python3-colcon-ros',
            'python3-colcon-test-result',
        ]
    elif 'catkin' not in pkg_names:
        debian_pkg_names += resolve_names(['catkin'], **context)
    print('Always install the following generic dependencies:')
    for debian_pkg_name in sorted(debian_pkg_names):
        print('  -', debian_pkg_name)

    debian_pkg_versions = {}

    # get build dependencies and map them to binary packages
    build_depends = get_dependencies(
        pkgs.values(), 'build', _get_build_and_recursive_run_dependencies)
    debian_pkg_names_building = resolve_names(build_depends, **context)
    debian_pkg_names_building -= set(debian_pkg_names)
    debian_pkg_names += order_dependencies(debian_pkg_names_building)
    debian_pkg_versions.update(
        get_binary_package_versions(apt_cache, debian_pkg_names))

    # get run and test dependencies and map them to binary packages
    run_and_test_depends = get_dependencies(
        pkgs.values(), 'run and test', _get_run_and_test_dependencies)
    debian_pkg_names_testing = resolve_names(
        run_and_test_depends, **context)
    # all additional run/test dependencies
    # are added after the build dependencies
    # in order to reuse existing images in the docker container
    debian_pkg_names_testing -= set(debian_pkg_names)
    debian_pkg_versions.update(
        get_binary_package_versions(apt_cache, debian_pkg_names_testing))
    if args.testing:
        debian_pkg_names += order_dependencies(debian_pkg_names_testing)

    mapped_workspaces = [
        (workspace_root, '/tmp/ws%s' % (index if index > 1 else ''))
        for index, workspace_root in enumerate(args.workspace_root, 1)]

    parent_result_space = []
    if len(args.workspace_root) > 1:
        parent_result_space = ['/opt/ros/%s' % args.rosdistro_name] + \
            [mapping[1] for mapping in mapped_workspaces[:-1]]

    # generate Dockerfile
    data = {
        'os_name': args.os_name,
        'os_code_name': args.os_code_name,
        'arch': args.arch,

        'distribution_repository_urls': args.distribution_repository_urls,
        'distribution_repository_keys': get_distribution_repository_keys(
            args.distribution_repository_urls,
            args.distribution_repository_key_files),

        'rosdistro_name': args.rosdistro_name,

        'uid': get_user_id(),

        'build_tool': args.build_tool,
        'build_tool_args': args.build_tool_args,
        'build_tool_test_args': args.build_tool_test_args,
        'ros_version': args.ros_version,

        'build_environment_variables': ['%s=%s' % key_value for key_value in args.env_vars.items()],

        'dependencies': debian_pkg_names,
        'dependency_versions': debian_pkg_versions,
        'install_lists': [],

        'testing': args.testing,
        'run_abichecker': args.run_abichecker,
        'require_gpu_support': args.require_gpu_support,
        'workspace_root': mapped_workspaces[-1][1],
        'parent_result_space': parent_result_space,
    }
    create_dockerfile(
        'devel/devel_task.Dockerfile.em', data, args.dockerfile_dir)

    # output hints about necessary volumes to mount
    ros_buildfarm_basepath = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..'))
    print('Mount the following volumes when running the container:')
    print('  -v %s:/tmp/ros_buildfarm:ro' % ros_buildfarm_basepath)
    for mapping in mapped_workspaces:
        print('  -v %s:%s' % mapping)


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
    depends = [
        d for d in pkg.build_depends + pkg.buildtool_depends
        if d.evaluated_condition is not False]
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
        run_depends = [
            d for d in
            pkg.build_export_depends + pkg.buildtool_export_depends +
            pkg.exec_depends
            if d.evaluated_condition is not False]
        depends += run_depends

        # consider recursive dependencies
        run_depends_in_pkgs.update(
            [d.name for d in run_depends if d.name in other_pkgs_by_names])

    return depends


def _get_run_and_test_dependencies(pkg, pkgs):
    return [
        d for d in
        pkg.build_export_depends + pkg.buildtool_export_depends +
        pkg.exec_depends + pkg.test_depends
        if d.evaluated_condition is not False]


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


def order_dependencies(binary_package_names):
    return sorted(binary_package_names)


if __name__ == '__main__':
    main()
