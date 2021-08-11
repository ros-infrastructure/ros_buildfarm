# Copyright 2020 Open Source Robotics Foundation, Inc.
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

import os
import subprocess

from ros_buildfarm.common import get_os_package_name


def _get_source_tag(
        rosdistro_name, pkg_name, pkg_version, os_name, os_code_name):
    assert os_name in ['fedora', 'rhel']
    return 'rpm/%s-%s_%s' % (
        get_os_package_name(rosdistro_name, pkg_name),
        pkg_version, os_code_name)


def build_sourcerpm(
        rosdistro_index_url, rosdistro_name, pkg_name, os_name, os_code_name,
        sources_dir):
    from rosdistro import get_cached_distribution
    from rosdistro import get_index
    index = get_index(rosdistro_index_url)
    dist_file = get_cached_distribution(index, rosdistro_name)
    if pkg_name not in dist_file.release_packages:
        return 'Not a released package name: %s' % pkg_name

    pkg = dist_file.release_packages[pkg_name]
    repo_name = pkg.repository_name
    repo = dist_file.repositories[repo_name]
    if not repo.release_repository.version:
        return "Repository '%s' has no release version" % repo_name

    pkg_version = repo.release_repository.version
    tag = _get_source_tag(
        rosdistro_name, pkg_name, pkg_version, os_name, os_code_name)
    os_pkg_name = get_os_package_name(rosdistro_name, pkg_name)
    release_repository_url = repo.release_repository.url

    clone_cmd = [
        'git', 'clone',
        '--branch', tag,
        # fetch all branches and tags but no history
        '--depth', '1', '--no-single-branch',
        release_repository_url, os_pkg_name]

    cmd = [
        'mock',
        '--scm-option', 'git_get=%s' % ' '.join(clone_cmd),
        '--scm-option', 'package=%s' % os_pkg_name,
        '--scm-option', 'branch=%s' % tag,
        '--scm-option', 'spec=rpm/%s.spec' % os_pkg_name,
        '--scm-enable',
        '--enable-network',
        '--disable-plugin', 'root_cache',
        '--resultdir', '%s' % sources_dir,
        '--no-cleanup-after',
        '--postinstall',
        '--verbose',
        '--root', 'ros_buildfarm',
        '--buildsrpm']

    print("Invoking '%s'" % ' '.join(cmd))
    subprocess.check_call(cmd)

    mock_root_path = subprocess.check_output(
        ['mock', '--root', 'ros_buildfarm', '--print-root-path']).decode('utf-8').strip()
    mock_sources_path = os.path.join(mock_root_path, 'builddir', 'build', 'SOURCES')

    # output package maintainers for job notification
    from catkin_pkg.package import parse_package
    pkg = parse_package(mock_sources_path)
    maintainer_emails = set([])
    for m in pkg.maintainers:
        maintainer_emails.add(m.email)
    if maintainer_emails:
        print('Package maintainer emails: %s' % (
            ' '.join(sorted(maintainer_emails))))
