from gzip import GzipFile
import hashlib
from io import BytesIO
import logging
import os
import socket
import time
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import urlopen

from collections import namedtuple

from .common import get_debian_package_name

MaintainerDescriptor = namedtuple('Maintainer', 'name email')

Target = namedtuple('Target', 'os_code_name arch')


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

    def __init__(self, name):
        self.name = name


def get_rosdistro_info(dist, build_file):
    all_pkg_names = dist.release_packages.keys()
    pkg_names = build_file.filter_packages(all_pkg_names)

    packages = {}
    for pkg_name in pkg_names:
        # package name
        ros_pkg = RosPackage(pkg_name)
        ros_pkg.debian_name = get_debian_package_name(dist.name, pkg_name)

        pkg = dist.release_packages[pkg_name]
        repo = dist.repositories[pkg.repository_name].release_repository
        # package version
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
        pkg_xml = dist.get_release_package_xml(pkg_name)
        if pkg_xml is not None:
            from catkin_pkg.package import InvalidPackage, parse_package_string
            try:
                pkg_manifest = parse_package_string(pkg_xml)
                for m in pkg_manifest.maintainers:
                    ros_pkg.maintainers.append(
                        MaintainerDescriptor(m.name, m.email))
                for u in pkg_manifest['urls']:
                    if u.type == 'website':
                        ros_pkg.url = u.url
                        break
            except InvalidPackage:
                pass

        packages[pkg_name] = ros_pkg
    return packages


def get_debian_repo_data(debian_repository_baseurl, targets, cache_dir):
    data = {}
    for target in targets:
        index = get_debian_repo_index(
            debian_repository_baseurl, target, cache_dir)
        data[target] = index
    return data


def get_debian_repo_index(debian_repository_baseurl, target, cache_dir):
    url = os.path.join(
        debian_repository_baseurl, 'dists', target.os_code_name, 'main')
    if target.arch == 'source':
        url = os.path.join(url, 'source', 'Sources.gz')
    else:
        url = os.path.join(url, 'binary-%s' % target.arch, 'Packages.gz')

    cache_filename = os.path.join(
        cache_dir, hashlib.md5(url.encode()).hexdigest())
    if not os.path.exists(cache_filename):
        fetch_gzip_url(url, cache_filename)

    logging.debug('Reading file: %s' % cache_filename)
    # split package blocks
    with open(cache_filename, 'r') as f:
        blocks = f.read().split('\n\n')
    blocks = [b.splitlines() for b in blocks if b]

    # extract version number of every package
    package_versions = {}
    for lines in blocks:
        prefix = 'Package: '
        assert lines[0].startswith(prefix)
        debian_pkg_name = lines[0][len(prefix):]

        prefix = 'Version: '
        versions = [l[len(prefix):] for l in lines if l.startswith(prefix)]
        version = versions[0] if len(versions) == 1 else None

        package_versions[debian_pkg_name] = version

    return package_versions


def fetch_gzip_url(url, dst_filename):
    dst_dirname = os.path.dirname(dst_filename)
    if not os.path.exists(dst_dirname):
        os.makedirs(dst_dirname)
    logging.debug('Downloading gz url: %s' % url)
    gz_str = load_url(url)
    gz_stream = BytesIO(gz_str)
    g = GzipFile(fileobj=gz_stream, mode='rb')
    with open(dst_filename, 'wb') as f:
        f.write(g.read())


def load_url(url, retry=2, retry_period=1, timeout=10):
    try:
        fh = urlopen(url, timeout=timeout)
    except HTTPError as e:
        if e.code == 503 and retry:
            time.sleep(retry_period)
            return load_url(
                url, retry=retry - 1, retry_period=retry_period,
                timeout=timeout)
        e.msg += ' (%s)' % url
        raise
    except URLError as e:
        if isinstance(e.reason, socket.timeout) and retry:
            time.sleep(retry_period)
            return load_url(
                url, retry=retry - 1, retry_period=retry_period,
                timeout=timeout)
        raise URLError(str(e) + ' (%s)' % url)
    return fh.read()
