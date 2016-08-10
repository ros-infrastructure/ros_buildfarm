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

from collections import namedtuple
from distutils.version import LooseVersion
import itertools
import os
import re
import shutil
import sys
import time

from .common import get_debian_package_name
from .common import get_release_view_name
from .common import get_short_arch
from .common import Target
from .config import get_index as get_config_index
from .config import get_release_build_files
from .debian_repo import get_debian_repo_data
from .status_page_input import get_rosdistro_info
from .status_page_input import RosPackage
from .templates import expand_template
from .templates import get_template_path


def build_release_status_page(
        config_url, rosdistro_name, release_build_name,
        cache_dir, output_dir, copy_resources=False):
    from rosdistro import get_cached_distribution
    from rosdistro import get_index

    start_time = time.time()

    config = get_config_index(config_url)
    release_build_files = get_release_build_files(config, rosdistro_name)
    build_file = release_build_files[release_build_name]

    index = get_index(config.rosdistro_index_url)

    # get targets
    targets = []
    for os_name in sorted(build_file.targets.keys()):
        if os_name not in ['debian', 'ubuntu']:
            continue
        for os_code_name in sorted(build_file.targets[os_name].keys()):
            targets.append(Target(os_name, os_code_name, 'source'))
            for arch in sorted(build_file.targets[os_name][os_code_name]):
                targets.append(Target(os_name, os_code_name, arch))
    print('The build file contains the following targets:')
    for _, os_code_name, arch in targets:
        print('  - %s %s' % (os_code_name, arch))

    # get all input data
    dist = get_cached_distribution(index, rosdistro_name)

    rosdistro_info = get_rosdistro_info(dist, build_file)

    # derive testing and main urls from building url
    building_repo_url = build_file.target_repository
    base_url = os.path.dirname(building_repo_url)
    testing_repo_url = os.path.join(base_url, 'testing')
    main_repo_url = os.path.join(base_url, 'main')

    building_repo_data = get_debian_repo_data(
        building_repo_url, targets, cache_dir)
    testing_repo_data = get_debian_repo_data(
        testing_repo_url, targets, cache_dir)
    main_repo_data = get_debian_repo_data(main_repo_url, targets, cache_dir)

    repos_data = [building_repo_data, testing_repo_data, main_repo_data]

    # compute derived attributes
    package_descriptors = get_rosdistro_package_descriptors(
        rosdistro_info, rosdistro_name)

    affected_by_sync = get_affected_by_sync(
        package_descriptors, targets, testing_repo_data, main_repo_data)

    regressions = get_regressions(
        package_descriptors, targets,
        building_repo_data, testing_repo_data, main_repo_data)

    version_status = get_version_status(
        package_descriptors, targets, repos_data, strip_version=True)

    homogeneous = get_homogeneous(package_descriptors, targets, repos_data)

    package_counts = get_package_counts(
        package_descriptors, targets, repos_data)

    jenkins_job_urls = get_jenkins_job_urls(
        rosdistro_name, config.jenkins_url, release_build_name, targets)

    # generate output
    repo_urls = [building_repo_url, testing_repo_url, main_repo_url]
    repo_names = get_url_names(repo_urls)

    ordered_pkgs = []
    for pkg_name in sorted(rosdistro_info.keys()):
        ordered_pkgs.append(rosdistro_info[pkg_name])

    template_name = 'status/release_status_page.html.em'
    data = {
        'title': 'ROS %s - release status' % rosdistro_name.capitalize(),
        'start_time': start_time,
        'start_time_local_str': time.strftime('%Y-%m-%d %H:%M:%S %z', time.localtime(start_time)),

        'resource_hashes': get_resource_hashes(),

        'repo_names': repo_names,
        'repo_urls': repo_urls,

        'has_repository_column': True,
        'has_status_column': True,
        'has_maintainer_column': True,

        'ordered_pkgs': ordered_pkgs,
        'targets': targets,
        'short_arches': dict(
            [(t.arch, get_short_arch(t.arch)) for t in targets]),
        'repos_data': repos_data,

        'affected_by_sync': affected_by_sync,
        'homogeneous': homogeneous,
        'jenkins_job_urls': jenkins_job_urls,
        'package_counts': package_counts,
        'regressions': regressions,
        'version_status': version_status,
    }
    html = expand_template(template_name, data)
    output_filename = os.path.join(
        output_dir, 'ros_%s_%s.html' % (rosdistro_name, release_build_name))
    print("Generating status page '%s':" % output_filename)
    with open(output_filename, 'w') as h:
        h.write(html)

    additional_resources(output_dir, copy_resources=copy_resources)


def build_debian_repos_status_page(
        repo_urls, os_code_name_and_arch_tuples,
        cache_dir, output_name, output_dir):
    start_time = time.time()

    # get targets
    targets = []
    for os_code_name_and_arch in os_code_name_and_arch_tuples:
        assert os_code_name_and_arch.count(':') == 1, \
            'The string (%s) does not contain single colon separating an ' + \
            'OS code name and an architecture'
        os_code_name, arch = os_code_name_and_arch.split(':')
        targets.append(Target('ubuntu', os_code_name, arch))

    # get all input data
    repos_data = []
    for repo_url in repo_urls:
        repo_data = get_debian_repo_data(repo_url, targets, cache_dir)
        repos_data.append(repo_data)

    # compute derived attributes
    package_descriptors = get_repos_package_descriptors(repos_data, targets)

    version_status = get_version_status(
        package_descriptors, targets, repos_data, strip_os_code_name=True)

    homogeneous = get_homogeneous(package_descriptors, targets, repos_data)

    package_counts = get_package_counts(
        package_descriptors, targets, repos_data)

    # generate output
    repo_names = get_url_names(repo_urls)

    ordered_pkgs = []
    for debian_pkg_name in sorted(package_descriptors.keys()):
        pkg = RosPackage(debian_pkg_name)
        pkg.debian_name = debian_pkg_name
        pkg.version = package_descriptors[debian_pkg_name].version

        # set unavailable attributes
        pkg.repository_name = None
        pkg.repository_url = None
        pkg.status = None
        pkg.status_description = None
        pkg.maintainers = []
        pkg.url = None

        ordered_pkgs.append(pkg)

    template_name = 'status/release_status_page.html.em'
    data = {
        'title': 'ROS repository status',
        'start_time': start_time,
        'start_time_local_str': time.strftime('%Y-%m-%d %H:%M:%S %z', time.localtime(start_time)),

        'resource_hashes': get_resource_hashes(),

        'repo_names': repo_names,
        'repo_urls': repo_urls,

        'has_repository_column': False,
        'has_status_column': False,
        'has_maintainer_column': False,

        'ordered_pkgs': ordered_pkgs,
        'targets': targets,
        'short_arches': dict(
            [(t.arch, get_short_arch(t.arch)) for t in targets]),
        'repos_data': repos_data,

        'affected_by_sync': None,
        'homogeneous': homogeneous,
        'jenkins_job_urls': None,
        'package_counts': package_counts,
        'regressions': None,
        'version_status': version_status,
    }
    html = expand_template(template_name, data)
    output_filename = os.path.join(
        output_dir, '%s.html' % output_name)
    print("Generating status page '%s':" % output_filename)
    with open(output_filename, 'w') as h:
        h.write(html)

    additional_resources(output_dir)


PackageDescriptor = namedtuple(
    'PackageDescriptor', 'pkg_name debian_pkg_name version')


def get_rosdistro_package_descriptors(rosdistro_info, rosdistro_name):
    descriptors = {}
    for pkg_name, pkg in rosdistro_info.items():
        debian_pkg_name = get_debian_package_name(rosdistro_name, pkg_name)
        descriptors[pkg_name] = PackageDescriptor(
            pkg_name, debian_pkg_name, pkg.version)
    return descriptors


def get_repos_package_descriptors(repos_data, targets):
    descriptors = {}
    # the highest version is the reference
    for target in targets:
        for repo_data in repos_data:
            repo_index = repo_data[target]
            for debian_pkg_name, version in repo_index.items():
                version = _strip_os_code_name_suffix(
                    version, target.os_code_name)
                if debian_pkg_name not in descriptors:
                    descriptors[debian_pkg_name] = PackageDescriptor(
                        debian_pkg_name, debian_pkg_name, version)
                    continue
                if not version:
                    continue
                other_version = descriptors[debian_pkg_name].version
                if not other_version:
                    continue
                # update version if higher
                if _version_is_gt_other(version, other_version):
                    descriptors[debian_pkg_name] = PackageDescriptor(
                        debian_pkg_name, debian_pkg_name, version)
    return descriptors


def get_url_names(urls):
    names = []
    for url in urls:
        basename = os.path.basename(url)
        if basename == 'ubuntu':
            basename = os.path.basename(os.path.dirname(url))
        names.append(basename)
    return names


def get_affected_by_sync(
        package_descriptors, targets,
        testing_repo_data, main_repo_data):
    """
    For each package and target check if it is affected by a sync.

    This is the case when the package version in the testing repo is different
    from the version in the main repo.

    :return: a dict indexed by package names containing
      dicts indexed by targets containing a boolean flag
    """
    affected_by_sync = {}
    for package_descriptor in package_descriptors.values():
        pkg_name = package_descriptor.pkg_name
        debian_pkg_name = package_descriptor.debian_pkg_name

        affected_by_sync[pkg_name] = {}
        for target in targets:
            testing_version = _strip_version_suffix(
                testing_repo_data.get(target, {}).get(debian_pkg_name, None))
            main_version = _strip_version_suffix(
                main_repo_data.get(target, {}).get(debian_pkg_name, None))

            affected_by_sync[pkg_name][target] = \
                testing_version != main_version
    return affected_by_sync


def get_regressions(
        package_descriptors, targets,
        building_repo_data, testing_repo_data, main_repo_data):
    """
    For each package and target check if it is a regression.

    This is the case if the main repo contains a package version which is
    higher then in any of the other repos or if any of the other repos does not
    contain that package at all.

    :return: a dict indexed by package names containing
      dicts indexed by targets containing a boolean flag
    """
    regressions = {}
    for package_descriptor in package_descriptors.values():
        pkg_name = package_descriptor.pkg_name
        debian_pkg_name = package_descriptor.debian_pkg_name

        regressions[pkg_name] = {}
        for target in targets:
            regressions[pkg_name][target] = False
            main_version = \
                main_repo_data.get(target, {}).get(debian_pkg_name, None)
            if main_version is not None:
                main_ver_loose = LooseVersion(main_version)
                for repo_data in [building_repo_data, testing_repo_data]:
                    version = \
                        repo_data.get(target, {}).get(debian_pkg_name, None)
                    if not version or main_ver_loose > LooseVersion(version):
                        regressions[pkg_name][target] = True
    return regressions


def get_version_status(
        package_descriptors, targets, repos_data,
        strip_version=False, strip_os_code_name=False):
    """
    For each package and target check if it is affected by a sync.

    This is the case when the package version in the testing repo is different
    from the version in the main repo.

    :return: a dict indexed by package names containing
      dicts indexed by targets containing
      a list of status strings (one for each repo)
    """
    status = {}
    for package_descriptor in package_descriptors.values():
        pkg_name = package_descriptor.pkg_name
        debian_pkg_name = package_descriptor.debian_pkg_name
        ref_version = package_descriptor.version
        if strip_version:
            ref_version = _strip_version_suffix(ref_version)

        status[pkg_name] = {}
        for target in targets:
            statuses = []
            for repo_data in repos_data:
                version = repo_data.get(target, {}).get(debian_pkg_name, None)
                if strip_version:
                    version = _strip_version_suffix(version)
                if strip_os_code_name:
                    version = _strip_os_code_name_suffix(
                        version, target.os_code_name)

                if ref_version:
                    if not version:
                        statuses.append('missing')
                    elif version.startswith(ref_version):  # including equal
                        statuses.append('equal')
                    else:
                        if _version_is_gt_other(version, ref_version):
                            statuses.append('higher')
                        else:
                            statuses.append('lower')
                else:
                    if not version:
                        statuses.append('ignore')
                    else:
                        statuses.append('obsolete')
            status[pkg_name][target] = statuses
    return status


version_regex = re.compile(r'[0-9.-]+[0-9]')


def _strip_version_suffix(version):
    """
    Remove trailing junk from the version number.

    >>> strip_version_suffix('')
    ''
    >>> strip_version_suffix('None')
    'None'
    >>> strip_version_suffix('1.2.3-4trusty-20140131-1359-+0000')
    '1.2.3-4'
    >>> strip_version_suffix('1.2.3-foo')
    '1.2.3'
    """
    global version_regex
    if not version:
        return version
    match = version_regex.search(version)
    return match.group(0) if match else version


def _strip_os_code_name_suffix(version, os_code_name):
    if version:
        index = version.find(os_code_name)
        if index != -1:
            version = version[:index]
    return version


def get_homogeneous(package_descriptors, targets, repos_data):
    """
    For each package check if the version in one repo is equal for all targets.

    The version could be different in different repos though.

    :return: a dict indexed by package names containing a boolean flag
    """
    homogeneous = {}
    for package_descriptor in package_descriptors.values():
        pkg_name = package_descriptor.pkg_name
        debian_pkg_name = package_descriptor.debian_pkg_name

        versions = []
        for repo_data in repos_data:
            versions.append(set([]))
            for target in targets:
                version = _strip_version_suffix(
                    repo_data.get(target, {}).get(debian_pkg_name, None))
                versions[-1].add(version)
        homogeneous[pkg_name] = max([len(v) for v in versions]) == 1
    return homogeneous


def get_package_counts(package_descriptors, targets, repos_data):
    """
    Get the number of packages per target and repository.

    :return: a dict indexed by targets containing
      a list of integer values (one for each repo)
    """
    counts = {}
    for target in targets:
        counts[target] = [0] * len(repos_data)
    for package_descriptor in package_descriptors.values():
        debian_pkg_name = package_descriptor.debian_pkg_name

        for target in targets:
            for i, repo_data in enumerate(repos_data):
                version = repo_data.get(target, {}).get(debian_pkg_name, None)
                if version:
                    counts[target][i] += 1
    return counts


def get_jenkins_job_urls(
        rosdistro_name, jenkins_url, release_build_name, targets):
    """
    Get the Jenkins job urls for each target.

    The placeholder {pkg} needs to be replaced with the ROS package name.

    :return: a dict indexed by targets containing a string
    """
    urls = {}
    for target in targets:
        view_name = get_release_view_name(
            rosdistro_name, release_build_name,
            target.os_name, target.os_code_name, target.arch)
        base_url = jenkins_url + '/view/%s/job/%s__{pkg}__' % \
            (view_name, view_name)
        if target.arch == 'source':
            urls[target] = base_url + '%s_%s__source' % \
                (target.os_name, target.os_code_name)
        else:
            urls[target] = base_url + '%s_%s_%s__binary' % \
                (target.os_name, target.os_code_name, target.arch)
    return urls


def additional_resources(output_dir, copy_resources=False):
    for subfolder in ['css', 'js']:
        dst = os.path.join(output_dir, subfolder)
        if not os.path.exists(dst):
            src = get_template_path(os.path.join('status', subfolder))
            if copy_resources:
                shutil.copytree(src, dst)
            else:
                os.symlink(os.path.abspath(src), dst)


def get_resource_hashes():
    hashes = {}
    for subfolder in ['css', 'js']:
        path = get_template_path(os.path.join('status', subfolder))
        for filename in os.listdir(path):
            if filename.endswith('.%s' % subfolder):
                with open(os.path.join(path, filename)) as f:
                    hashes[filename] = hash(tuple(f.read()))
    return hashes


def _version_is_gt_other(version, other_version):
    try:
        # might raise TypeError: http://bugs.python.org/issue14894
        return LooseVersion(version) > LooseVersion(other_version)
    except TypeError:
        loose_version, other_loose_version = \
            _get_comparable_loose_versions(version, other_version)
        return loose_version < other_loose_version


def _get_comparable_loose_versions(version_str1, version_str2):
    loose_version1 = LooseVersion(version_str1)
    loose_version2 = LooseVersion(version_str2)
    if sys.version_info[0] > 2:
        # might raise TypeError in Python 3: http://bugs.python.org/issue14894
        version_parts1 = loose_version1.version
        version_parts2 = loose_version2.version
        for i in range(min(len(version_parts1), len(version_parts2))):
            try:
                version_parts1[i] < version_parts2[i]
            except TypeError:
                version_parts1[i] = str(version_parts1[i])
                version_parts2[i] = str(version_parts2[i])
    return loose_version1, loose_version2


def build_release_compare_page(
        config_url, rosdistro_names,
        output_dir, copy_resources=False):
    from rosdistro import get_cached_distribution
    from rosdistro import get_index

    start_time = time.time()

    config = get_config_index(config_url)

    index = get_index(config.rosdistro_index_url)

    # get all input data
    distros = [get_cached_distribution(index, d) for d in rosdistro_names]

    repo_names = [d.repositories.keys() for d in distros]
    repo_names = [x for y in repo_names for x in y]

    repos_data = {}
    for repo_name in repo_names:
        repo_data = _compare_repo_version(distros, repo_name)
        if repo_data:
            repos_data[repo_name] = repo_data

    template_name = 'status/release_compare_page.html.em'
    data = {
        'title':
            'ROS %s - version compare' % ' '.join([x.capitalize() for x in rosdistro_names]),

        'start_time': start_time,
        'start_time_local_str': time.strftime('%Y-%m-%d %H:%M:%S %z', time.localtime(start_time)),

        'resource_hashes': get_resource_hashes(),

        'rosdistro_names': rosdistro_names,

        'repos_data': repos_data,
    }
    html = expand_template(template_name, data)
    output_filename = os.path.join(
        output_dir, 'compare_%s.html' % '_'.join(rosdistro_names))
    print("Generating compare page: '%s'" % output_filename)
    with open(output_filename, 'w') as h:
        h.write(html)

    additional_resources(output_dir, copy_resources=copy_resources)


class CompareRow(object):

    def __init__(self, repo_name):
        self.repo_name = repo_name
        self.repo_urls = []
        self.maintainers = {}
        self.versions = []
        self.branches = []

    def get_repo_name_with_link(self):
        valid_urls = [u for u in self.repo_urls if u]
        if len(set(valid_urls)) == 1:
            return '<a href="%s">%s</a>' % (valid_urls[0], self.repo_name)

        unique_urls = []
        [unique_urls.append(u) for u in valid_urls if u not in unique_urls]
        parts = [self.repo_name]
        for i, repo_url in enumerate(unique_urls):
            parts.append(' [<a href="%s">%d</a>]' % (repo_url, i + 1))
        return ' '.join(parts)

    def get_maintainers(self):
        return ' '.join([self.maintainers[k] for k in sorted(self.maintainers.keys())])

    def get_labels(self, distros):
        all_versions = [LooseVersion(v) if v else v for v in self.versions]
        valid_versions = [v for v in all_versions if v]
        labels = []
        if any([
            _is_only_patch_is_different(p[0], p[1])
            for p in itertools.combinations(valid_versions, 2)]
        ):
            labels.append('DIFF_PATCH')
        if any([_is_greater(p[0], p[1]) for p in itertools.combinations(valid_versions, 2)]):
            labels.append('DOWNGRADE_VERSION')

        versions_and_branches = zip(
            itertools.combinations(all_versions, 2), itertools.combinations(self.branches, 2))
        if any([
            _is_same_version_but_different_branch(vb[0][0], vb[0][1], vb[1][0], vb[1][1])
            for vb in versions_and_branches
        ]):
            labels.append('DIFF_BRANCH_SAME_VERSION')
        return labels


def _is_only_patch_is_different(a, b):
    return a.version[0] == b.version[0] and \
        a.version[1] == b.version[1] and a.version[2] != b.version[2]


def _is_greater(a, b):
    return a.version[0] > b.version[0] or \
        (a.version[0] == b.version[0] and a.version[1] > b.version[1])


def _is_same_version_but_different_branch(version_a, version_b, branch_a, branch_b):
    # skip when any version is unknown
    if not version_a or not version_b:
        return False
    # skip when any branch is unknown or they are equal
    if not branch_a or not branch_b or branch_a == branch_b:
        return False
    return version_a.version[0] == version_b.version[0] and \
        version_a.version[1] == version_b.version[1]


def _compare_repo_version(distros, repo_name):
    from catkin_pkg.package import InvalidPackage, parse_package_string
    row = CompareRow(repo_name)
    for distro in distros:
        repo_url = None
        version = None
        branch = None
        if repo_name in distro.repositories:
            repo = distro.repositories[repo_name]

            rel_repo = repo.release_repository
            if rel_repo:
                version = rel_repo.version
                for pkg_name in rel_repo.package_names:
                    pkg_xml = distro.get_release_package_xml(pkg_name)
                    if pkg_xml is not None:
                        try:
                            pkg = parse_package_string(pkg_xml)
                            for m in pkg.maintainers:
                                row.maintainers[m.name] = '<a href="mailto:%s">%s</a>' % \
                                    (m.email, m.name)
                        except InvalidPackage:
                            row.maintainers['zzz'] = '<b>invalid package.xml in %s</b>' % \
                                distro.name

                    if repo.source_repository:
                        repo_url = repo.source_repository.url
                    elif repo.doc_repository:
                        repo_url = repo.doc_repository.url

            source_repo = repo.source_repository
            if source_repo:
                branch = source_repo.version
            else:
                doc_repo = repo.source_repository
                if doc_repo:
                    branch = doc_repo.version

        row.repo_urls.append(repo_url)
        row.versions.append(version)
        row.branches.append(branch)

    # skip if no versions available
    if not [v for v in row.versions if v]:
        return None

    data = [row.get_repo_name_with_link(), row.get_maintainers()] + \
        [v if v else '' for v in row.versions]

    labels = row.get_labels(distros)
    if len(labels) > 0:
        data[0] += ' <span class="ht">%s</span>' % ' '.join(labels)

    # div-wrap all cells for layout reasons
    for i, value in enumerate(data):
        data[i] = '<div>%s</div>' % value

    return data
