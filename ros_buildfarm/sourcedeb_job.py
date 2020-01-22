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
from urllib.error import HTTPError
from urllib.request import urlretrieve

from ros_buildfarm.common import get_os_package_name
from ros_buildfarm.release_common import dpkg_parsechangelog


def get_sources(
        rosdistro_index_url, rosdistro_name, pkg_name, os_name, os_code_name,
        sources_dir, debian_repository_urls):
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

    cmd = [
        'git', 'clone',
        '--branch', tag,
        # fetch all branches and tags but no history
        '--depth', '1', '--no-single-branch',
        repo.release_repository.url, sources_dir]

    print("Invoking '%s'" % ' '.join(cmd))
    subprocess.check_call(cmd)

    # ensure that the package version is correct
    source_version = dpkg_parsechangelog(sources_dir, ['Version'])[0]
    if not source_version.startswith(pkg_version) or \
            (len(source_version) > len(pkg_version) and
             source_version[len(pkg_version)] in '0123456789'):
        raise RuntimeError(
            ('The cloned package version from the GBP (%s) does not match ' +
             'the expected package version from the distribution file (%s)') %
            (source_version, pkg_version))

    # If a tarball already exists reuse it
    origtgz_version = pkg_version.split('-')[0]
    debian_package_name = get_os_package_name(rosdistro_name, pkg_name)
    filename = '%s_%s.orig.tar.gz' % (debian_package_name, origtgz_version)

    URL_TEMPLATE = '%s/pool/main/%s/%s/%s'
    prefix = debian_package_name[0]
    for repo in debian_repository_urls:
        url = URL_TEMPLATE % (repo, prefix, debian_package_name, filename)

        output_file = os.path.join(sources_dir, '..', filename)
        try:
            urlretrieve(url, output_file)
            print("Downloaded original tarball '%s' to '%s'" %
                  (url, output_file))
            break
        except HTTPError:
            print("No tarball found at '%s'" % url)

    # output package version for job description
    print("Package '%s' version: %s" % (pkg_name, source_version))

    # output package maintainers for job notification
    from catkin_pkg.package import parse_package
    pkg = parse_package(sources_dir)
    maintainer_emails = set([])
    for m in pkg.maintainers:
        maintainer_emails.add(m.email)
    if maintainer_emails:
        print('Package maintainer emails: %s' %
              ' '.join(sorted(maintainer_emails)))


def _get_source_tag(
        rosdistro_name, pkg_name, pkg_version, os_name, os_code_name):
    assert os_name in ['debian', 'ubuntu']
    return 'debian/%s_%s_%s' % \
        (get_os_package_name(rosdistro_name, pkg_name),
         pkg_version, os_code_name)


def build_sourcedeb(sources_dir, os_name=None, os_code_name=None):
    cmd = [
        'gbp', 'buildpackage',
        '--git-ignore-new',
        '--git-ignore-branch',
        # dpkg-buildpackage args
        '-S']
    debian_before_stretch = ('squeeze', 'wheezy', 'jessie')
    ubuntu_before_artful = (
        'precise', 'quantal', 'raring', 'saucy',
        'trusty', 'utopic', 'vivid', 'wily',
        'xenial', 'yakkety', 'zesty')
    if (
        os_name == 'debian' and os_code_name not in debian_before_stretch or
        os_name == 'ubuntu' and os_code_name not in ubuntu_before_artful
    ):
        # don't fail for not installed build dependencies
        cmd.append('-d')
        # do not sign the .buildinfo file, since dpkg 1.18.19
        cmd.append('-ui')

    cmd += [
        # dpkg-buildpackage args
        '-us', '-uc',
        # debuild args for lintian
        '--lintian-opts', '--suppress-tags', 'newer-standards-version']

    # workaround for old gbp.conf values
    # https://github.com/ros-infrastructure/bloom/issues/211
    config_cmd = [
        'git', 'config',
        '--file', 'debian/gbp.conf',
        'git-buildpackage.upstream-tree']
    upstream_tree = subprocess.check_output(config_cmd, cwd=sources_dir)
    upstream_tree = upstream_tree.decode().rstrip()
    if upstream_tree != 'tag':
        config_cmd = [
            'git', 'config',
            '--file', 'debian/gbp.conf',
            'git-buildpackage.upstream-branch']
        upstream_tag = subprocess.check_output(config_cmd, cwd=sources_dir)
        upstream_tag = upstream_tag.decode().rstrip()
        cmd += [
            '--git-upstream-tag=' + upstream_tag,
            '--git-upstream-tree=tag']

    # workaround different default compression levels
    # resulting in different checksums for the tarball
    if (os_name, os_code_name) in (('ubuntu', 'zesty'), ('debian', 'stretch')):
        env = dict(os.environ)
        env['GZIP'] = '-9'
    else:
        env = None
    print("Invoking '%s' in '%s'" % (' '.join(cmd), sources_dir))
    subprocess.check_call(cmd, cwd=sources_dir, env=env)
