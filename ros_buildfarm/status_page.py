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

from collections import defaultdict
from collections import namedtuple
from distutils.version import LooseVersion
import itertools
import os
import re
import shutil
import sys
import time

import yaml

from .common import get_os_package_name
from .common import get_release_view_name
from .common import get_short_arch
from .common import get_short_os_code_name
from .common import get_short_os_name
from .common import package_format_mapping
from .common import Target
from .config import get_index as get_config_index
from .config import get_release_build_files
from .package_repo import get_package_repo_data
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
        if os_name not in ['debian', 'fedora', 'rhel', 'ubuntu']:
            continue
        for os_code_name in sorted(build_file.targets[os_name].keys()):
            targets.append(Target(os_name, os_code_name, 'source'))
            for arch in sorted(build_file.targets[os_name][os_code_name]):
                targets.append(Target(os_name, os_code_name, arch))
    if not targets:
        print('The build file contains no supported targets', file=sys.stderr)
        return
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

    building_repo_data = get_package_repo_data(
        building_repo_url, targets, cache_dir)
    testing_repo_data = get_package_repo_data(
        testing_repo_url, targets, cache_dir)
    main_repo_data = get_package_repo_data(main_repo_url, targets, cache_dir)

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
        'title': 'ROS packages for %s' % rosdistro_name.capitalize(),
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
        'short_code_names': {
            t.os_code_name: get_short_os_code_name(t.os_code_name) for t in targets},
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

    yaml_folder = os.path.join(output_dir, 'yaml')
    if not os.path.exists(yaml_folder):
        os.mkdir(yaml_folder)

    yaml_filename = os.path.join(
        yaml_folder, 'ros_%s_%s.yaml' % (rosdistro_name, release_build_name))
    write_yaml(yaml_filename, ordered_pkgs, repos_data)


def build_debian_repos_status_page(
        rosdistro_name, repo_urls, os_code_name_and_arch_tuples,
        cache_dir, output_name, output_dir):
    os_name_and_os_code_name_and_arch_tuples = []
    for os_code_name_and_arch in os_code_name_and_arch_tuples:
        assert os_code_name_and_arch.count(':') == 1, \
            'The string (%s) does not contain single colon separating an ' + \
            'OS code name and an architecture'
        os_code_name, arch = os_code_name_and_arch.split(':')
        os_name_and_os_code_name_and_arch_tuples.append(('ubuntu', os_code_name, arch))

    return build_repos_status_page(
        rosdistro_name, repo_urls, os_name_and_os_code_name_and_arch_tuples,
        cache_dir, output_name, output_dir)


def build_repos_status_page(
        rosdistro_name, repo_urls, os_name_and_os_code_name_and_arch_tuples,
        cache_dir, output_name, output_dir):
    start_time = time.time()

    # get targets
    targets = []
    for os_name, os_code_name, arch in os_name_and_os_code_name_and_arch_tuples:
        targets.append(Target(os_name, os_code_name, arch))

    # get all input data
    repos_data = []
    for repo_url in repo_urls:
        repo_data = get_package_repo_data(repo_url, targets, cache_dir)
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
        'title': 'All packages for %s targets' % rosdistro_name.capitalize(),
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
        'short_code_names': {
            t.os_code_name: get_short_os_code_name(t.os_code_name) for t in targets},
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
    'PackageDescriptor', 'pkg_name debian_pkg_name version source_name')


def get_rosdistro_package_descriptors(rosdistro_info, rosdistro_name):
    descriptors = {}
    for pkg_name, pkg in rosdistro_info.items():
        debian_pkg_name = get_os_package_name(rosdistro_name, pkg_name)
        descriptors[pkg_name] = PackageDescriptor(
            pkg_name, debian_pkg_name, pkg.version, debian_pkg_name)
    return descriptors


def get_repos_package_descriptors(repos_data, targets):
    descriptors = {}
    # the highest version is the reference
    for target in targets:
        for repo_data in repos_data:
            repo_index = repo_data[target]
            for debian_pkg_name, repo_descriptor in repo_index.items():
                version = _strip_os_code_name_suffix(repo_descriptor.version, target)
                if debian_pkg_name not in descriptors:
                    descriptors[debian_pkg_name] = PackageDescriptor(
                        debian_pkg_name, debian_pkg_name, version, repo_descriptor.source_name)
                    continue
                if not version:
                    continue
                other_version = descriptors[debian_pkg_name].version
                if not other_version:
                    continue
                # update version if higher
                if _version_is_gt_other(version, other_version):
                    descriptors[debian_pkg_name] = PackageDescriptor(
                        debian_pkg_name, debian_pkg_name, version, repo_descriptor.source_name)
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
                _get_pkg_version(testing_repo_data, target, debian_pkg_name))
            main_version = _strip_version_suffix(
                _get_pkg_version(main_repo_data, target, debian_pkg_name))

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
                _get_pkg_version(main_repo_data, target, debian_pkg_name)
            if main_version is not None:
                main_ver_loose = LooseVersion(main_version)
                for repo_data in [building_repo_data, testing_repo_data]:
                    version = \
                        _get_pkg_version(repo_data, target, debian_pkg_name)
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
        source_pkg_name = package_descriptor.source_name
        ref_version = package_descriptor.version
        if strip_version:
            ref_version = _strip_version_suffix(ref_version)

        status[pkg_name] = {}
        for target in targets:
            statuses = []
            for repo_data in repos_data:
                version = _get_pkg_version(repo_data, target, debian_pkg_name)
                if strip_version:
                    version = _strip_version_suffix(version)
                if strip_os_code_name:
                    version = _strip_os_code_name_suffix(version, target)

                if ref_version:
                    if not version:
                        if target.arch == 'source' and \
                                source_pkg_name and debian_pkg_name != source_pkg_name:
                            statuses.append('ignore')
                        else:
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


def _strip_os_code_name_suffix(version, target):
    if version:
        if package_format_mapping[target.os_name] == 'rpm':
            delimiter = '.' + get_short_os_name(target.os_name) + target.os_code_name
        else:
            delimiter = target.os_code_name
        index = version.find(delimiter)
        if index != -1:
            version = version[:index]
    return version


def _get_pkg_version(repo_data, target, package_name):
    repo_pkg_descriptor = repo_data.get(target, {}).get(package_name, None)
    return repo_pkg_descriptor.version if repo_pkg_descriptor else None


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
                    _get_pkg_version(repo_data, target, debian_pkg_name))
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
                version = _get_pkg_version(repo_data, target, debian_pkg_name)
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


def build_blocked_releases_page(
    config_url, rosdistro_name,
    output_dir, repo_names=None, copy_resources=False
):
    start_time = time.localtime()

    repos_info = _get_blocked_releases_info(config_url, rosdistro_name, repo_names=repo_names)
    repos_data = [_format_repo_table_row(name, data) for name, data in sorted(repos_info.items())]

    template_name = 'status/blocked_releases_page.html.em'
    data = {
        'title': 'ROS %s - blocked releases' % rosdistro_name,
        'start_time': time.strftime('%Y-%m-%d %H:%M:%S %z', start_time),

        'resource_hashes': get_resource_hashes(),

        'rosdistro_name': rosdistro_name.capitalize(),

        'repos_data': repos_data,
    }
    html = expand_template(template_name, data)
    output_filename = os.path.join(
        output_dir, 'blocked_releases_%s.html' % rosdistro_name)
    print("Generating blocked releases page '%s':" % output_filename)
    with open(output_filename, 'w') as h:
        h.write(html)

    additional_resources(output_dir, copy_resources=copy_resources)


def build_blocked_source_entries_page(
        config_url, rosdistro_name,
        output_dir, copy_resources=False
):
    start_time = time.localtime()

    repos_info = _get_blocked_source_entries_info(config_url, rosdistro_name)

    # Expand a template for the webpage
    repos_data = [_format_repo_table_row(name, data) for name, data in sorted(repos_info.items())]
    template_name = 'status/blocked_source_entries_page.html.em'
    data = {
        'title': 'ROS %s - blocked source entries' % rosdistro_name,
        'start_time': time.strftime('%Y-%m-%d %H:%M:%S %z', start_time),
        'resource_hashes': get_resource_hashes(),
        'rosdistro_name': rosdistro_name.capitalize(),
        'repos_data': repos_data,
    }
    output_filename = os.path.join(
        output_dir, 'blocked_source_entries_%s.html' % rosdistro_name)
    print("Generating blocked source entries page '%s':" % output_filename)
    with open(output_filename, 'w') as h:
        h.write(expand_template(template_name, data))
    additional_resources(output_dir, copy_resources=copy_resources)


def _div_wrap(data, name=None):
    if_attr = ' id="%s"' % name if name is not None else ''
    return '<div{0}>{1}</div>'.format(if_attr, data)


def _filter_tag_wrap(label):
    return '<span class="ht">label="{0}"</span>'.format(label)


def _name_query_wrap(name):
    try:
        from urllib.parse import quote
    except ImportError:
        from urllib import quote
    query = 'id="{0}"'.format(name)
    return '<a href="?q={0}">{1}</a>'.format(quote(query), name)


def _format_repo_table_row(name, data):
    # convert data in dictionary into data that can be used as an html table row
    row = {}

    repos_blocking = data.get('repos_blocking', [])
    repos_blocked_by = data.get('repos_blocked_by', {})

    # tags for filtering
    tags = ''
    if data.get('released', False):
        tags += _filter_tag_wrap('RELEASED')
    else:
        tags += _filter_tag_wrap('UNRELEASED')

        if len(repos_blocked_by) > 0:
            tags += _filter_tag_wrap('BLOCKED')
        elif len(repos_blocking) > 0:
            tags += _filter_tag_wrap('UNBLOCKED')
            tags += _filter_tag_wrap('UNBLOCKED_BLOCKING')
        else:
            tags += _filter_tag_wrap('UNBLOCKED')
            tags += _filter_tag_wrap('UNBLOCKED_UNBLOCKING')

    url = data.get('url', None)
    if url:
        name_html = '<a href="{0}">{1}</a>'.format(url, name)
    else:
        name_html = name
    name_cell = name_html + tags

    # repo name cell
    row['name'] = _div_wrap(name_cell, name)

    # whether or not the repo has been released
    row['version'] = _div_wrap(data.get('version', 'Not released'))

    # num repos blocked by
    row['num_repos_blocked_by'] = _div_wrap(len(repos_blocked_by))

    # repos blocked by
    row['repos_blocked_by'] = _div_wrap('<br />'.join(
        _name_query_wrap(repo) for repo in sorted(repos_blocked_by.keys())))

    # maintainers info
    maintainers = data.get('maintainers', {})
    maintainers_cell = ''
    for repo_name in sorted(maintainers.keys()):
        maintainers_cell += repo_name + ':<br />'
        maintainers_cell += '<br />'.join(
            '<a href="mailto:{0}" style="padding-left: 1em">{1}</a>'
            .format(maintainers[repo_name][name], name)
            for name in sorted(maintainers[repo_name].keys()))
        maintainers_cell += '<br />'
    row['maintainers_of_repos_blocked_by'] = _div_wrap(maintainers_cell)

    # num repos blocking recursively
    row['num_repos_recursively_blocked'] = _div_wrap(
        len(data.get('recursive_repos_blocking', [])))

    # num repos blocking
    row['num_repos_blocked'] = _div_wrap(len(repos_blocking))

    # repos blocking by not being released
    row['repos_blocked'] = _div_wrap('<br />'.join(
        _name_query_wrap(repo) for repo in sorted(repos_blocking)))

    return row


def _get_blocked_releases_info(config_url, rosdistro_name, repo_names=None):
    import rosdistro
    from rosdistro.dependency_walker import DependencyWalker

    config = get_config_index(config_url)

    index = rosdistro.get_index(config.rosdistro_index_url)

    print('Checking packages for "%s" distribution' % rosdistro_name)

    # Find the previous distribution to the current one
    try:
        prev_rosdistro_name = _prev_rosdistro(index, rosdistro_name)
    except ValueError as e:
        print(e.args[0], file=sys.stderr)
        exit(-1)

    cache = rosdistro.get_distribution_cache(index, rosdistro_name)
    distro_file = cache.distribution_file

    prev_cache = rosdistro.get_distribution_cache(index, prev_rosdistro_name)
    prev_distribution = rosdistro.get_cached_distribution(
        index, prev_rosdistro_name, cache=prev_cache)

    prev_distro_file = prev_cache.distribution_file

    dependency_walker = DependencyWalker(prev_distribution)

    # Check missing dependencies for packages that were in the previous
    # distribution that have not yet been released in the current distribution
    # Filter repos without a version or a release repository
    prev_repo_names = set(_released_repos(prev_distro_file))

    if repo_names is not None:
        ignored_inputs = prev_repo_names.difference(repo_names)
        prev_repo_names.intersection_update(repo_names)
        repo_names = prev_repo_names

        if len(ignored_inputs) > 0:
            print(
                'Ignoring inputs for which repository info not found in previous distribution '
                '(did you list a package instead of a repository?):')
            print('\n'.join(
                sorted('\t{0}'.format(repo) for repo in ignored_inputs)))

    current_repo_names = set(_released_repos(distro_file))

    # Get a list of currently released packages
    current_package_names = set(_released_packages(distro_file, current_repo_names))

    released_repos = prev_repo_names.intersection(
        current_repo_names)

    if prev_repo_names.issubset(current_repo_names):
        print('All inputs already released in {0}.'.format(rosdistro_name))

    repos_info = defaultdict(dict)
    unprocessed_repos = prev_repo_names
    while unprocessed_repos:
        print('Processing repos:\n%s' %
              '\n'.join(['- %s' % r for r in sorted(unprocessed_repos)]))
        new_repos_to_process = set()  # set containing repos that come up while processing others

        for repo_name in unprocessed_repos:
            repos_info[repo_name]['released'] = repo_name in released_repos

            if repo_name in released_repos:
                repo = distro_file.repositories[repo_name]
                version = repo.release_repository.version
                repos_info[repo_name]['version'] = version

            else:
                # Gather info on which required repos have not been released yet
                # Assume dependencies will be the same as in the previous distribution and find
                # which ones have been released
                repo = prev_distro_file.repositories[repo_name]
                release_repo = repo.release_repository
                package_dependencies = set()
                packages = release_repo.package_names
                # Accumulate all dependencies for those packages
                for package in packages:
                    package_dependencies.update(_package_dependencies(dependency_walker, package))

                # For all package dependencies, check if they are released yet
                unreleased_pkgs = package_dependencies.difference(
                    current_package_names)
                # Remove the packages which this repo provides
                unreleased_pkgs = unreleased_pkgs.difference(packages)

                # Get maintainer info and repo of unreleased packages
                maintainers = defaultdict(dict)
                repos_blocked_by = set()
                for pkg_name in unreleased_pkgs:
                    unreleased_repo_name = \
                        prev_distro_file.release_packages[pkg_name].repository_name
                    repos_blocked_by.add(unreleased_repo_name)
                    maintainers[unreleased_repo_name].update(
                        dict(_maintainers(prev_distribution, pkg_name)))
                if maintainers:
                    repos_info[repo_name]['maintainers'] = maintainers

                repos_info[repo_name]['repos_blocked_by'] = {}
                for blocking_repo_name in repos_blocked_by:
                    # Get url of blocking repos
                    repo_url = _repo_url(prev_distribution, blocking_repo_name)
                    repos_info[repo_name]['repos_blocked_by'].update(
                        {blocking_repo_name: repo_url})

                    # Mark blocking relationship in other direction
                    if blocking_repo_name not in repos_info:
                        new_repos_to_process.add(blocking_repo_name)
                        repos_info[blocking_repo_name] = {}
                    if 'repos_blocking' not in repos_info[blocking_repo_name]:
                        repos_info[blocking_repo_name]['repos_blocking'] = set([])
                    repos_info[blocking_repo_name]['repos_blocking'].add(repo_name)

            # Get url of repo
            repo_url = _repo_url(prev_distribution, repo_name)
            if repo_url:
                repos_info[repo_name]['url'] = repo_url

            new_repos_to_process.discard(repo_name)  # this repo has been fully processed now

        for repo_name in repos_info.keys():
            # Recursively get all repos being blocked by this repo
            recursive_blocks = set([])
            repos_to_check = set([repo_name])
            while repos_to_check:
                next_repo_to_check = repos_to_check.pop()
                blocks = repos_info[next_repo_to_check].get('repos_blocking', set([]))
                new_blocks = blocks - recursive_blocks
                repos_to_check |= new_blocks
                recursive_blocks |= new_blocks
            if recursive_blocks:
                repos_info[repo_name]['recursive_repos_blocking'] = recursive_blocks
        unprocessed_repos = new_repos_to_process

    return repos_info


def _get_blocked_source_entries_info(config_url, rosdistro_name):
    from rosdistro import get_cached_distribution
    from rosdistro import get_index
    from rosdistro.dependency_walker import DependencyWalker

    config = get_config_index(config_url)
    index = get_index(config.rosdistro_index_url)

    print('Getting blocked source entries for', rosdistro_name)

    try:
        prev_rosdistro_name = _prev_rosdistro(index, rosdistro_name)
    except ValueError as e:
        print(e.args[0], file=sys.stderr)
        exit(-1)

    print('Comparing', rosdistro_name, 'with', prev_rosdistro_name)

    dist = get_cached_distribution(index, rosdistro_name)
    prev_dist = get_cached_distribution(index, prev_rosdistro_name)

    prev_walker = DependencyWalker(prev_dist)

    prev_released_repos = set(_released_repos(prev_dist))
    source_entry_repos = set(_source_entry_repos(dist))
    missing_repos = prev_released_repos.difference(source_entry_repos)

    # Assume repos will provide the same packages as previous distro
    missing_packages = set(_released_packages(prev_dist, missing_repos))

    repos_info = defaultdict(dict)

    # Give all repos some basic info
    for repo_name in prev_released_repos.union(source_entry_repos).union(missing_repos):
        repos_info[repo_name]['url'] = ''
        repos_info[repo_name]['repos_blocking'] = set()
        repos_info[repo_name]['recursive_repos_blocking'] = set()
        repos_info[repo_name]['released'] = False
        repos_info[repo_name]['version'] = 'no'
        repos_info[repo_name]['repos_blocked_by'] = {}
        repos_info[repo_name]['maintainers'] = defaultdict(dict)

    for repo_name in prev_released_repos:
        repos_info[repo_name]['url'] = _repo_url(prev_dist, repo_name)

    # has a source entry? Call that 'released' with a 'version' to reuse _format_repo_table_row
    for repo_name in source_entry_repos:
        repos_info[repo_name]['released'] = True
        repos_info[repo_name]['version'] = 'yes'

    # Determine which repos directly block the missing ones
    for repo_name in missing_repos:
        package_dependencies = set()
        for pkg in _released_packages(prev_dist, (repo_name,)):
            package_dependencies.update(_package_dependencies(prev_walker, pkg))

        for dep in package_dependencies:
            if dep in missing_packages:
                blocking_repo = prev_dist.release_packages[dep].repository_name
                if blocking_repo == repo_name:
                    # ignore packages in the same repo
                    continue
                repos_info[repo_name]['repos_blocked_by'][blocking_repo] = \
                    _repo_url(prev_dist, repo_name)
                repos_info[repo_name]['maintainers'][blocking_repo].update(
                    dict(_maintainers(prev_dist, dep)))

                # Mark blocking relationship in other direction
                repos_info[blocking_repo]['repos_blocking'].add(repo_name)

    # Compute which repos block another recursively
    for repo_name in repos_info.keys():
        checked_repos = set()
        repos_to_check = set([repo_name])
        while repos_to_check:
            next_repo = repos_to_check.pop()
            new_repos_blocking = repos_info[next_repo]['repos_blocking']
            repos_info[repo_name]['recursive_repos_blocking'].update(new_repos_blocking)
            checked_repos.add(next_repo)
            repos_to_check.update(repos_info[next_repo]['repos_blocking'].difference(checked_repos))

    return repos_info


def _prev_rosdistro(index, rosdistro_name):
    """Given current rosdistro name, return the previous."""
    valid_rosdistro_names = list(index.distributions.keys())
    valid_rosdistro_names.sort()

    # skip distributions with a different type if the information is available
    distro_type = index.distributions[rosdistro_name].get('distribution_type')
    if distro_type is not None:
        valid_rosdistro_names = [
            n for n in valid_rosdistro_names
            if distro_type == index.distributions[n].get('distribution_type')]

    try:
        i = valid_rosdistro_names.index(rosdistro_name)
    except ValueError:
        raise ValueError('Distribution key not found in list of valid distributions.')

    if i == 0:
        raise ValueError('No previous distribution found.')

    return valid_rosdistro_names[i - 1]


def _released_repos(distro):
    for repo_name in distro.repositories.keys():
        if _is_released(repo_name, distro):
            yield repo_name


def _is_released(repo, dist_file):
    return repo in dist_file.repositories and \
        dist_file.repositories[repo].release_repository is not None and \
        dist_file.repositories[repo].release_repository.version is not None


def _source_entry_repos(distro):
    for repo_name in distro.repositories.keys():
        if _has_source_entry(repo_name, distro):
            yield repo_name


def _has_source_entry(repo_name, dist_file):
    return repo_name in dist_file.repositories and \
        dist_file.repositories[repo_name].source_repository is not None and \
        dist_file.repositories[repo_name].source_repository.url is not None


def _package_dependencies(walker, package):
    try:
        for dep in walker.get_recursive_depends(
                package, ['build', 'buildtool', 'run', 'test'], ros_packages_only=True,
                limit_depth=1):
            yield dep
    except AssertionError as e:
        print(e, file=sys.stderr)


def _released_packages(distro, repo_names):
    for repo in repo_names:
        for package_name in distro.repositories[repo].release_repository.package_names:
            yield package_name


def _repo_url(distro, repo_name):
    repo_url = None
    if repo_name in distro.repositories:
        repo = distro.repositories[repo_name]
        if repo.source_repository:
            repo_url = repo.source_repository.url
        elif repo.doc_repository:
            repo_url = repo.doc_repository.url
    return repo_url


def _maintainers(distro, pkg_name):
    from catkin_pkg.package import InvalidPackage, parse_package_string
    pkg_xml = distro.get_release_package_xml(pkg_name)
    if pkg_xml is not None:
        try:
            pkg = parse_package_string(pkg_xml)
        except InvalidPackage:
            pass
        else:
            for m in pkg.maintainers:
                yield m.name, m.email


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

    pkg_names = [d.release_packages.keys() for d in distros]
    pkg_names = [x for y in pkg_names for x in y]

    pkgs_data = {}
    for pkg_name in pkg_names:
        pkg_data = _compare_package_version(distros, pkg_name)
        if pkg_data:
            pkgs_data[pkg_name] = pkg_data

    template_name = 'status/release_compare_page.html.em'
    data = {
        'title': 'ROS packages in %s' % ' '.join([x.capitalize() for x in rosdistro_names]),

        'start_time': start_time,
        'start_time_local_str': time.strftime('%Y-%m-%d %H:%M:%S %z', time.localtime(start_time)),

        'resource_hashes': get_resource_hashes(),

        'rosdistro_names': rosdistro_names,

        'pkgs_data': pkgs_data,
    }
    html = expand_template(template_name, data)
    output_filename = os.path.join(
        output_dir, 'compare_%s.html' % '_'.join(rosdistro_names))
    print("Generating compare page: '%s'" % output_filename)
    with open(output_filename, 'w') as h:
        h.write(html)

    additional_resources(output_dir, copy_resources=copy_resources)


class CompareRow(object):

    def __init__(self, pkg_name):  # noqa: D107
        self.pkg_name = pkg_name
        self.repo_name = ''
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


def _compare_package_version(distros, pkg_name):
    from catkin_pkg.package import InvalidPackage, parse_package_string
    row = CompareRow(pkg_name)
    for distro in distros:
        repo_url = None
        version = None
        branch = None
        if pkg_name in distro.release_packages:
            pkg = distro.release_packages[pkg_name]
            row.repo_name = pkg.repository_name
            repo = distro.repositories[pkg.repository_name]

            rel_repo = repo.release_repository
            if rel_repo:
                version = rel_repo.version
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

    data = [row.pkg_name, row.get_repo_name_with_link(), row.get_maintainers()] + \
        [v if v else '' for v in row.versions]

    labels = row.get_labels(distros)
    if len(labels) > 0:
        data[1] += ' <span class="ht">%s</span>' % ' '.join(labels)

    # div-wrap all cells for layout reasons
    for i, value in enumerate(data):
        data[i] = '<div>%s</div>' % value

    return data


REPOS_DATA_NAMES = ['build', 'test', 'main']


def write_yaml(yaml_filename, ordered_pkgs, repos_data):
    print("Generating status yaml '%s':" % yaml_filename)
    summary = {}
    for pkg in ordered_pkgs:
        pkg_d = {'version': pkg.version, 'url': pkg.repository_url, 'status': pkg.status}
        if pkg.status_description:
            pkg_d['status_description'] = pkg.status_description
        pkg_d['maintainers'] = [{'email': m.email, 'name': m.name} for m in pkg.maintainers]

        pkg_d['build_status'] = {}

        for name, repo_set in zip(REPOS_DATA_NAMES, repos_data):
            for key, build_data in repo_set.items():
                if pkg.debian_name not in build_data:
                    continue

                # Dynamically Create the Nested Dictionary
                d = pkg_d['build_status']
                for field in [key.os_name, key.os_code_name, key.arch]:
                    if field not in d:
                        d[field] = {}
                    d = d[field]
                d[name] = str(build_data[pkg.debian_name].version)
        summary[pkg.name] = pkg_d

    with open(yaml_filename, 'w') as f:
        yaml.safe_dump(summary, f, allow_unicode=True)
