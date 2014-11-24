#!/usr/bin/env python3

import argparse
import os
import sys

from apt import Cache
from catkin_pkg.packages import find_packages
from ros_buildfarm.argument import add_argument_distribution_repository_key_files
from ros_buildfarm.argument import add_argument_distribution_repository_urls
from ros_buildfarm.argument import add_argument_dockerfile_dir
from ros_buildfarm.common import get_binary_package_versions
from ros_buildfarm.common import get_distribution_repository_keys
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
        required=True,
        help='The root path of the workspace to compile')
    parser.add_argument(
        '--os-name',
        required=True,
        help="The OS name (e.g. 'ubuntu')")
    parser.add_argument(
        '--os-code-name',
        required=True,
        help="The OS code name (e.g. 'trusty')")
    add_argument_distribution_repository_urls(parser)
    add_argument_distribution_repository_key_files(parser)
    add_argument_dockerfile_dir(parser)
    parser.add_argument(
        '--testing',
        action='store_true',
        help='The flag if the workspace should be built with tests enabled '
             'and instead of installing the tests are ran')
    args = parser.parse_args(argv)

    # get direct build dependencies
    source_space = os.path.join(args.workspace_root, 'src')
    print("Crawling for packages in workspace '%s'" % source_space)
    pkgs = find_packages(source_space)

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

    debian_pkg_names = ['build-essential', 'python3']
    debian_pkg_versions = {}

    # get build dependencies and map them to binary packages
    build_depends = get_dependencies(
        pkgs.values(), 'build', _get_build_dependencies)
    debian_pkg_names_building = resolve_names(build_depends, **context)
    debian_pkg_names += sorted(debian_pkg_names_building)
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
        debian_pkg_names += sorted(debian_pkg_names_testing)

    # generate Dockerfile
    data = {
        'os_name': args.os_name,
        'os_code_name': args.os_code_name,

        'maintainer_email': 'dthomas+buildfarm@osrfoundation.org',
        'maintainer_name': 'Dirk Thomas',

        'distribution_repository_urls': args.distribution_repository_urls,
        'distribution_repository_keys': get_distribution_repository_keys(
            args.distribution_repository_urls,
            args.distribution_repository_key_files),

        'rosdistro_name': args.rosdistro_name,

        'uid': os.getuid(),

        'dependencies': list(debian_pkg_names),
        'dependency_versions': debian_pkg_versions,

        'testing': args.testing,
    }
    create_dockerfile(
        'devel/devel_task.Dockerfile.em', data, args.dockerfile_dir)

    # output hints about necessary volumes to mount
    ros_buildfarm_basepath = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..'))
    print('Mount the following volumes when running the container:')
    print('  -v %s:/tmp/ros_buildfarm:ro' % ros_buildfarm_basepath)
    print('  -v %s:/tmp/catkin_workspace' % args.workspace_root)


def get_dependencies(pkgs, label, get_dependencies_callback):
    depend_names = set([])
    for pkg in pkgs:
        depend_names.update([d.name for d in get_dependencies_callback(pkg)])
    print('Identified the following %s dependencies:' % label)
    for depend_name in sorted(depend_names):
        print('  -', depend_name)
    return depend_names


def _get_build_dependencies(pkg):
    return pkg.build_depends + pkg.buildtool_depends


def _get_run_and_test_dependencies(pkg):
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
    main()
