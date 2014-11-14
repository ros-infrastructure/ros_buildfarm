from distutils.version import LooseVersion
import os
import re
import time

from rosdistro import get_cached_distribution
from rosdistro import get_index
from rosdistro import get_release_build_files

from .common import get_debian_package_name
from .common import get_release_view_name
from .status_page_input import get_debian_repo_data
from .status_page_input import get_rosdistro_info
from .status_page_input import Target
from .templates import expand_template
from .templates import template_basepath


def build_release_status_page(
        rosdistro_index_url, rosdistro_name, release_build_name,
        building_repo_url, testing_repo_url, main_repo_url,
        cache_dir, output_dir):
    start_time = time.localtime()

    index = get_index(rosdistro_index_url)
    release_build_files = get_release_build_files(index, rosdistro_name)
    build_file = release_build_files[release_build_name]

    # get targets
    targets = []
    for os_name in build_file.get_target_os_names():
        if os_name != 'ubuntu':
            continue
        for os_code_name in build_file.get_target_os_code_names(os_name):
            targets.append(Target(os_code_name, 'source'))
            for arch in build_file.get_target_arches(os_name, os_code_name):
                targets.append(Target(os_code_name, arch))
    print('The build file contains the following targets:')
    for os_code_name, arch in targets:
        print('  - %s %s' % (os_code_name, arch))

    # get all input data
    dist = get_cached_distribution(index, rosdistro_name)

    rosdistro_info = get_rosdistro_info(dist, build_file)

    building_repo_data = get_debian_repo_data(
        building_repo_url, targets, cache_dir)
    testing_repo_data = get_debian_repo_data(
        testing_repo_url, targets, cache_dir)
    main_repo_data = get_debian_repo_data(main_repo_url, targets, cache_dir)

    repos_data = [building_repo_data, testing_repo_data, main_repo_data]

    # compute derived attributes
    affected_by_sync = get_affected_by_sync(
        rosdistro_name, targets,
        rosdistro_info, testing_repo_data, main_repo_data)

    regressions = get_regressions(
        rosdistro_name, targets,
        rosdistro_info, building_repo_data, testing_repo_data, main_repo_data)

    version_status = get_version_status(
        rosdistro_name, targets, rosdistro_info,
        repos_data)

    homogeneous = get_homogeneous(
        rosdistro_name, targets, rosdistro_info, repos_data)

    package_counts = get_package_counts(
        rosdistro_name, targets, rosdistro_info, repos_data)

    jenkins_job_urls = get_jenkins_job_urls(
        rosdistro_name, build_file.jenkins_url, release_build_name, targets)

    # generate output
    template_name = 'status/release_status_page.html.em'
    data = {
        'rosdistro_name': rosdistro_name,
        'start_time': time.strftime('%Y-%m-%d %H:%M:%S %Z', start_time),

        'resource_hashes': get_resource_hashes(),

        'repo_urls': [building_repo_url, testing_repo_url, main_repo_url],

        'rosdistro_info': rosdistro_info,
        'targets': targets,
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
        output_dir, '%s_%s.html' % (rosdistro_name, release_build_name))
    print("Generating status page '%s':" % output_filename)
    with open(output_filename, 'w') as h:
        h.write(html)

    additional_resources(output_dir)


def get_affected_by_sync(
        rosdistro_name, targets, rosdistro_info,
        testing_repo_data, main_repo_data):
    """
    For each package and target check if it is affected by a sync.

    This is the case when the package version in the testing repo is different
    from the version in the main repo.

    :return: a dict indexed by package names containing
      dicts indexed by targets containing a boolean flag
    """
    affected_by_sync = {}
    for pkg_name in rosdistro_info.keys():
        affected_by_sync[pkg_name] = {}
        debian_pkg_name = get_debian_package_name(rosdistro_name, pkg_name)

        for target in targets:
            testing_version = \
                (testing_repo_data[target][debian_pkg_name]
                 if debian_pkg_name in testing_repo_data[target] else None) \
                if target in testing_repo_data else None
            testing_version = _strip_version_suffix(testing_version)
            main_version = \
                (main_repo_data[target][debian_pkg_name]
                 if debian_pkg_name in main_repo_data[target] else None) \
                if target in main_repo_data else None
            main_version = _strip_version_suffix(main_version)

            affected_by_sync[pkg_name][target] = \
                testing_version != main_version
    return affected_by_sync


def get_regressions(
        rosdistro_name, targets, rosdistro_info,
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
    for pkg_name in rosdistro_info.keys():
        regressions[pkg_name] = {}
        debian_pkg_name = get_debian_package_name(rosdistro_name, pkg_name)

        for target in targets:
            regressions[pkg_name][target] = False
            main_version = \
                (main_repo_data[target][debian_pkg_name]
                 if debian_pkg_name in main_repo_data[target] else None) \
                if target in main_repo_data else None
            if main_version:
                for repo_data in [building_repo_data, testing_repo_data]:
                    version = \
                        (repo_data[target][debian_pkg_name]
                         if debian_pkg_name in repo_data[target] else None) \
                        if target in repo_data else None
                    if not version or \
                            LooseVersion(main_version) > LooseVersion(version):
                        regressions[pkg_name][target] = True
    return regressions


def get_version_status(rosdistro_name, targets, rosdistro_info, repos_data):
    """
    For each package and target check if it is affected by a sync.

    This is the case when the package version in the testing repo is different
    from the version in the main repo.

    :return: a dict indexed by package names containing
      dicts indexed by targets containing
      a list of status strings (one for each repo)
    """
    status = {}
    for pkg_name, pkg in rosdistro_info.items():
        status[pkg_name] = {}
        ref_version = pkg.version
        debian_pkg_name = get_debian_package_name(rosdistro_name, pkg_name)

        for target in targets:
            statuses = []
            for repo_data in repos_data:
                version = \
                    (repo_data[target][debian_pkg_name]
                     if debian_pkg_name in repo_data[target] else None) \
                    if target in repo_data else None
                version = _strip_version_suffix(version)

                if ref_version:
                    if not version:
                        statuses.append('missing')
                    elif version == ref_version:
                        statuses.append('equal')
                    elif LooseVersion(version) < LooseVersion(ref_version):
                        statuses.append('lower')
                    else:
                        statuses.append('higher')
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


def get_homogeneous(rosdistro_name, targets, rosdistro_info, repos_data):
    """
    For each package check if the version in one repo is equal for all targets.

    The version could be different in different repos though.

    :return: a dict indexed by package names containing a boolean flag
    """
    homogeneous = {}
    for pkg_name in rosdistro_info.keys():
        debian_pkg_name = get_debian_package_name(rosdistro_name, pkg_name)

        versions = []
        for repo_data in repos_data:
            versions.append(set([]))
            for target in targets:
                version = \
                    (repo_data[target][debian_pkg_name]
                     if debian_pkg_name in repo_data[target] else None) \
                    if target in repo_data else None
                version = _strip_version_suffix(version)
                versions[-1].add(version)
        homogeneous[pkg_name] = max([len(v) for v in versions]) == 1
    return homogeneous


def get_package_counts(rosdistro_name, targets, rosdistro_info, repos_data):
    """
    Get the number of packages per target and repository.

    :return: a dict indexed by targets containing
      a list of integer values (one for each repo)
    """
    counts = {}
    for target in targets:
        counts[target] = [0] * len(repos_data)
    for pkg_name in rosdistro_info.keys():
        debian_pkg_name = get_debian_package_name(rosdistro_name, pkg_name)

        for target in targets:
            for i, repo_data in enumerate(repos_data):
                version = \
                    (repo_data[target][debian_pkg_name]
                     if debian_pkg_name in repo_data[target] else None) \
                    if target in repo_data else None
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
    view_name = get_release_view_name(rosdistro_name, release_build_name)
    base_url = jenkins_url + '/view/%s/job/%s__{pkg}__ubuntu_' % \
        (view_name, view_name)
    for target in targets:
        if target.arch == 'source':
            urls[target] = base_url + '%s__source' % target.os_code_name
        else:
            urls[target] = base_url + '%s_%s__binary' % \
                (target.os_code_name, target.arch)
    return urls


def additional_resources(output_dir):
    for subfolder in ['css', 'js']:
        dst = os.path.join(output_dir, subfolder)
        if not os.path.exists(dst):
            src = os.path.join(template_basepath, 'status', subfolder)
            os.symlink(os.path.abspath(src), dst)


def get_resource_hashes():
    hashes = {}
    for subfolder in ['css', 'js']:
        path = os.path.join(template_basepath, 'status', subfolder)
        for filename in os.listdir(path):
            if filename.endswith('.%s' % subfolder):
                with open(os.path.join(path, filename)) as f:
                    hashes[filename] = hash(tuple(f.read()))
    return hashes
