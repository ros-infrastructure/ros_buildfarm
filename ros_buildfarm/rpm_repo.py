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

import logging
import os
from xml.dom import minidom

from .http_cache import fetch_and_cache_gzip
from .http_cache import fetch_and_cache_plaintext


def get_ros_rpm_repo_index(rpm_repository_baseurl, target, cache_dir):
    return get_rpm_repo_index(
        os.path.join(rpm_repository_baseurl, '$releasever', '$basearch'),
        target, cache_dir)


def get_rpm_repo_index(rpm_repository_baseurl, target, cache_dir):
    # These variables are often included in repository base URLs by YUM/DNF
    url = rpm_repository_baseurl.replace('$releasever', target.os_code_name)
    url = url.replace('$basearch', target.arch if target.arch != 'source' else 'SRPMS')

    repomd_url = os.path.join(url, 'repodata', 'repomd.xml')
    repomd_cache_filename = fetch_and_cache_plaintext(repomd_url, cache_dir)

    primary_xml_url = os.path.join(
        url, _get_primary_xml_location(repomd_cache_filename))
    primary_xml_cache_filename = fetch_and_cache_gzip(
        primary_xml_url, cache_dir)

    logging.debug('Reading file: %s' % primary_xml_cache_filename)
    pkgdb = minidom.parse(primary_xml_cache_filename)

    # extract version number of every package
    package_versions = {}
    for pkg in pkgdb.getElementsByTagName('package'):
        if pkg.getAttribute('type') != 'rpm':
            continue
        pkg_name = pkg.getElementsByTagName('name')[0].firstChild.data
        pkg_version_obj = pkg.getElementsByTagName('version')[0]
        pkg_version = pkg_version_obj.getAttribute('ver')
        pkg_release = pkg_version_obj.getAttribute('rel')
        package_versions[pkg_name] = pkg_version + '-' + pkg_release

    return package_versions


def _get_primary_xml_location(repomd_xml):
    logging.debug('Reading file: %s' % repomd_xml)
    repomd_data_elements = minidom.parse(
        repomd_xml).getElementsByTagName('data')

    for data_entry in repomd_data_elements:
        if data_entry.getAttribute('type') == 'primary':
            return data_entry.getElementsByTagName('location')[0].getAttribute('href').strip()

    raise Exception('Failed to determine location of primary XML')
