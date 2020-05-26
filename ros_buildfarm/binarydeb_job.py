# Copyright 2014, 2016 Open Source Robotics Foundation, Inc.
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
import sys
from time import gmtime, strftime
import traceback

from ros_buildfarm.common import get_os_package_name
from ros_buildfarm.release_common import dpkg_parsechangelog


def get_sourcedeb(
        rosdistro_index_url, rosdistro_name, package_name, sourcepkg_dir,
        skip_download_sourcepkg=False):
    # ensure that no source subfolder exists
    debian_package_name = get_os_package_name(rosdistro_name, package_name)
    subfolders = _get_package_subfolders(sourcepkg_dir, debian_package_name)
    assert not subfolders, \
        ("Sourcedeb directory '%s' must not have any " +
         "subfolders starting with '%s-'") % (sourcepkg_dir, package_name)

    debian_package_name = get_os_package_name(rosdistro_name, package_name)
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

        # get the exact sourcedeb version
        showsrc_output = subprocess.check_output([
            'apt-cache', 'showsrc', debian_package_name]).decode()
        line_prefix = 'Version: '
        debian_package_versions = [
            line[len(line_prefix):] for line in showsrc_output.splitlines()
            if line.startswith(line_prefix + package_version)]
        assert len(debian_package_versions) == 1, \
            "Failed to find sourcedeb with version '%s', only found: %s" % \
            (package_version, ', '.join(debian_package_versions))

        # download sourcedeb
        apt_script = os.path.join(
            os.path.dirname(__file__), 'wrapper', 'apt.py')
        cmd = [
            sys.executable, apt_script,
            'source', '--download-only', '--only-source',
            debian_package_name + '=' + debian_package_versions[0]]
        print("Invoking '%s'" % ' '.join(cmd))
        subprocess.check_call(cmd, cwd=sourcepkg_dir)

    # extract sourcedeb
    filenames = _get_package_dsc_filename(sourcepkg_dir, debian_package_name)
    assert len(filenames) == 1, filenames
    dsc_filename = filenames[0]
    cmd = ['dpkg-source', '-x', dsc_filename]
    print("Invoking '%s'" % ' '.join(cmd))
    subprocess.check_call(cmd, cwd=sourcepkg_dir)

    # ensure that one source subfolder exists
    subfolders = _get_package_subfolders(sourcepkg_dir, debian_package_name)
    assert len(subfolders) == 1, subfolders
    source_dir = subfolders[0]

    # output package maintainers for job notification
    from catkin_pkg.package import parse_package
    pkg = parse_package(source_dir)
    maintainer_emails = set([])
    for m in pkg.maintainers:
        maintainer_emails.add(m.email)
    if maintainer_emails:
        print('Package maintainer emails: %s' %
              ' '.join(sorted(maintainer_emails)))


def append_build_timestamp(rosdistro_name, package_name, sourcepkg_dir):
    # ensure that one source subfolder exists
    debian_package_name = get_os_package_name(rosdistro_name, package_name)
    subfolders = _get_package_subfolders(sourcepkg_dir, debian_package_name)
    assert len(subfolders) == 1, subfolders
    source_dir = subfolders[0]

    source, version, distribution, urgency = dpkg_parsechangelog(
        source_dir, ['Source', 'Version', 'Distribution', 'Urgency'])
    cmd = [
        'debchange',
        '-v',
        '%s.%s' % (version, strftime('%Y%m%d.%H%M%S', gmtime()))
        # Backwards compatibility for #460
        if rosdistro_name not in (
            'indigo', 'jade', 'kinetic', 'lunar', 'ardent')
        else '%s-%s' % (version, strftime('%Y%m%d-%H%M%S%z')),
        '-p',  # preserve directory name
        '-D', distribution,
        '-u', urgency,
        '-m',  # keep maintainer details
        'Append timestamp when binarydeb was built.',
    ]
    print("Invoking '%s' in '%s'" % (' '.join(cmd), source_dir))
    subprocess.check_call(cmd, cwd=source_dir)


def build_binarydeb(rosdistro_name, package_name, sourcepkg_dir):
    # ensure that one source subfolder exists
    debian_package_name = get_os_package_name(rosdistro_name, package_name)
    subfolders = _get_package_subfolders(sourcepkg_dir, debian_package_name)
    assert len(subfolders) == 1, subfolders
    source_dir = subfolders[0]

    source, version = dpkg_parsechangelog(
        source_dir, ['Source', 'Version'])
    # output package version for job description
    print("Package '%s' version: %s" % (debian_package_name, version))

    cmd = ['apt-src', 'import', source, '--here', '--version', version]
    subprocess.check_call(cmd, cwd=source_dir)

    cmd = ['apt-src', 'build', source]
    print("Invoking '%s' in '%s'" % (' '.join(cmd), source_dir))
    try:
        subprocess.check_call(cmd, cwd=source_dir)
    except subprocess.CalledProcessError:
        traceback.print_exc()
        sys.exit("""
--------------------------------------------------------------------------------------------------
`{0}` failed.
This is usually because of an error building the package.
The traceback from this failure (just above) is printed for completeness, but you can ignore it.
You should look above `E: Building failed` in the build log for the actual cause of the failure.
--------------------------------------------------------------------------------------------------
""".format(' '.join(cmd)))


def _get_package_subfolders(basepath, debian_package_name):
    subfolders = []
    for filename in os.listdir(basepath):
        path = os.path.join(basepath, filename)
        if not os.path.isdir(path):
            continue
        if filename.startswith('%s-' % debian_package_name):
            subfolders.append(path)
    return subfolders


def _get_package_dsc_filename(basepath, debian_package_name):
    filenames = []
    for filename in os.listdir(basepath):
        if filename.startswith('%s_' % debian_package_name) and \
                filename.endswith('.dsc'):
            filenames.append(filename)
    return filenames
