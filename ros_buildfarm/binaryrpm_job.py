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

import glob
import os
import subprocess

from ros_buildfarm.common import get_os_package_name


def get_sourcerpm(
        rosdistro_index_url, rosdistro_name, package_name, sourcepkg_dir,
        skip_download_sourcepkg=False):
    # ensure that no source subfolder exists
    rpm_package_name = get_os_package_name(rosdistro_name, package_name)
    if not skip_download_sourcepkg:
        # get expected package version from rosdistro
        from rosdistro import get_distribution_cache
        from rosdistro import get_index
        index = get_index(rosdistro_index_url)
        dist_cache = get_distribution_cache(index, rosdistro_name)
        dist_file = dist_cache.distribution_file
        assert package_name in dist_file.release_packages
        pkg = dist_file.release_packages[package_name]
        repo = dist_file.repositories[pkg.repository_name]
        package_version = repo.release_repository.version

        cmd = [
            'mock',
            '--resultdir', '%s' % sourcepkg_dir,
            '--no-cleanup-after',
            '--verbose',
            '--root', 'ros_buildfarm',
            '--dnf-cmd', '--', 'download', '--source',
            '--disablerepo', '*',
            '--enablerepo', 'ros-buildfarm-target-source',
            '%s-%s.*' % (rpm_package_name, package_version)]

        print("Invoking '%s'" % ' '.join(cmd))
        subprocess.check_call(cmd, cwd=sourcepkg_dir)


def build_binaryrpm(
        rosdistro_name, package_name, sourcepkg_dir, binarypkg_dir, append_timestamp=False):
    rpm_package_name = get_os_package_name(rosdistro_name, package_name)
    source_packages = glob.glob(os.path.join(sourcepkg_dir, rpm_package_name + '-*.src.rpm'))
    assert len(source_packages) == 1

    cmd = [
        'mock',
        '--enable-network',
        '--resultdir', '%s' % binarypkg_dir,
        '--no-cleanup-after',
        '--verbose',
        '--root', 'ros_buildfarm',
        '--postinstall',
        '--rebuild', source_packages[0]]

    if append_timestamp:
        cmd += ['--define', 'dist_suffix .%(date -u +%%Y%%m%%d.%%H%%M%%S)']

    print("Invoking '%s'" % ' '.join(cmd))
    subprocess.check_call(cmd)

    mock_root_path = subprocess.check_output(
        ['mock', '--root', 'ros_buildfarm', '--print-root-path']).decode('utf-8').strip()
    mock_build_path = os.path.join(mock_root_path, 'builddir', 'build', 'BUILD')
    package_root = os.path.join(mock_build_path, os.listdir(mock_build_path)[0])

    # output package maintainers for job notification
    from catkin_pkg.package import parse_package
    pkg = parse_package(package_root)
    maintainer_emails = set([])
    for m in pkg.maintainers:
        maintainer_emails.add(m.email)
    if maintainer_emails:
        print('Package maintainer emails: %s' %
              ' '.join(sorted(maintainer_emails)))
