# Copyright 2014 Open Source Robotics Foundation, Inc.
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

from collections import namedtuple

from .common import get_implicitly_ignored_package_names
from .common import get_os_package_name
from .common import get_package_manifests

MaintainerDescriptor = namedtuple('Maintainer', 'name email')


class RosPackage(object):

    __slots__ = [
        'name',
        'debian_name',
        'version',
        'url',
        'repository_name',
        'repository_url',
        'status',
        'status_description',
        'maintainers',
    ]

    def __init__(self, name):  # noqa: D107
        self.name = name


def get_rosdistro_info(dist, build_file):
    pkg_names = dist.release_packages.keys()
    cached_pkgs = get_package_manifests(dist)

    filtered_pkg_names = build_file.filter_packages(pkg_names)
    explicitly_ignored_without_recursion_pkg_names = \
        set(pkg_names) & set(build_file.package_ignore_list)
    explicitly_ignored_pkg_names = \
        set(pkg_names) - set(filtered_pkg_names) - explicitly_ignored_without_recursion_pkg_names
    if explicitly_ignored_pkg_names:
        implicitly_ignored_pkg_names = get_implicitly_ignored_package_names(
            cached_pkgs, explicitly_ignored_pkg_names)
        filtered_pkg_names = \
            set(filtered_pkg_names) - implicitly_ignored_pkg_names
    filtered_pkg_names = set(filtered_pkg_names) - explicitly_ignored_without_recursion_pkg_names

    packages = {}
    for pkg_name in pkg_names:
        # package name
        ros_pkg = RosPackage(pkg_name)
        ros_pkg.debian_name = get_os_package_name(dist.name, pkg_name)

        pkg = dist.release_packages[pkg_name]
        repo = dist.repositories[pkg.repository_name].release_repository
        # package version
        if not repo.version:
            continue
        ros_pkg.version = repo.version

        # repository name and url
        ros_pkg.repository_name = pkg.repository_name
        repo_url = repo.url
        other_repos = [
            dist.repositories[pkg.repository_name].source_repository,
            dist.repositories[pkg.repository_name].doc_repository]
        for other_repo in other_repos:
            if other_repo:
                repo_url = other_repo.url
                if repo_url.startswith('https://github.com/') and \
                        repo_url.endswith('.git'):
                    if other_repo.version:
                        repo_url = '%s/tree/%s' % \
                            (repo_url[:-4], other_repo.version)
                break
        ros_pkg.repository_url = repo_url

        # package status and description
        ros_pkg.status = 'unknown'
        ros_pkg.status_description = ''
        if dist.repositories[pkg.repository_name].status:
            ros_pkg.status = dist.repositories[pkg.repository_name].status
        if dist.repositories[pkg.repository_name].status_description:
            ros_pkg.status_description = \
                dist.repositories[pkg.repository_name].status_description

        # maintainers and package url from manifest
        ros_pkg.maintainers = []
        ros_pkg.url = None
        if pkg_name in cached_pkgs:
            pkg_manifest = cached_pkgs[pkg_name]
            for m in pkg_manifest.maintainers:
                ros_pkg.maintainers.append(
                    MaintainerDescriptor(m.name, m.email))
            for u in pkg_manifest['urls']:
                if u.type == 'website':
                    ros_pkg.url = u.url
                    break

        # handle ignored packages
        if pkg_name not in filtered_pkg_names:
            ros_pkg.version = None
            ros_pkg.status = 'disabled'
            ros_pkg.status_description = \
                'disabled by the release build configuration'

        packages[pkg_name] = ros_pkg
    return packages
