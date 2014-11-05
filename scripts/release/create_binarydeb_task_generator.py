#!/usr/bin/env python3

import argparse
import os
import sys

from rosdistro import get_distribution_file
from rosdistro import get_index

from apt import Cache
from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_binarydeb_dir
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_package_name
from ros_buildfarm.argument import add_argument_rosdistro_index_url
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.common import get_binary_package_versions
from ros_buildfarm.common import get_debian_package_name
from ros_buildfarm.common import get_distribution_repository_keys
from ros_buildfarm.templates import expand_template


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate a 'Dockerfile' for building the binarydeb")
    add_argument_rosdistro_index_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_package_name(parser)
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)  # TODO not yet supported
    parser.add_argument(
        '--distribution-repository-urls',
        nargs='*',
        default=[],
        help='The list of distribution repository URLs to use for installing '
             'dependencies')
    parser.add_argument(
        '--distribution-repository-key-files',
        nargs='*',
        default=[],
        help='The list of distribution repository key files to verify the '
             'corresponding URLs')
    add_argument_binarydeb_dir(parser)
    parser.add_argument(
        '--dockerfile-dir',
        default=os.curdir,
        help="The directory where the 'Dockerfile' will be generated")
    args = parser.parse_args(argv)

    debian_package_name = get_debian_package_name(
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
    debian_pkg_names = ['apt-src', 'devscripts']
    # TODO upload_binarydeb dependencies
    #debian_pkg_names += []

    # add build dependencies from .dsc file
    dsc_file = get_dsc_file(
        args.binarydeb_dir, debian_package_name, debian_package_version)
    debian_pkg_names += sorted(get_build_depends(dsc_file))

    # get versions for build dependencies
    apt_cache = Cache()
    debian_pkg_versions = get_binary_package_versions(
        apt_cache, debian_pkg_names)

    # generate Dockerfile
    data = {
        'os_name': args.os_name,
        'os_code_name': args.os_code_name,

        'maintainer_email': 'dthomas+buildfarm@osrfoundation.org',
        'maintainer_name': 'Dirk Thomas',

        'uid': os.getuid(),

        'distribution_repository_urls': args.distribution_repository_urls,
        'distribution_repository_keys': get_distribution_repository_keys(
            args.distribution_repository_urls,
            args.distribution_repository_key_files),

        'dependencies': list(debian_pkg_names),
        'dependency_versions': debian_pkg_versions,
    }
    content = expand_template('release/binarydeb_task.Dockerfile.em', data)
    dockerfile = os.path.join(args.dockerfile_dir, 'Dockerfile')
    print("Generating Dockerfile '%s':" % dockerfile)
    for line in content.splitlines():
        print(' ', line)
    with open(dockerfile, 'w') as h:
        h.write(content)

    # output hints about necessary volumes to mount
    ros_buildfarm_basepath = os.path.normpath(
        os.path.join(os.path.dirname(__file__), '..', '..'))
    print('Mount the following volumes when running the container:')
    print('  -v %s:/tmp/ros_buildfarm' % ros_buildfarm_basepath)
    print('  -v %s:/tmp/binarydeb' % args.binarydeb_dir)


def get_dsc_file(basepath, debian_package_name, debian_package_version):
    dsc_files = []
    for filename in os.listdir(basepath):
        if filename.startswith(
                '%s_%s' % (debian_package_name, debian_package_version)) and \
                filename.endswith('.dsc'):
            dsc_files.append(os.path.join(basepath, filename))
    assert len(dsc_files) == 1
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
