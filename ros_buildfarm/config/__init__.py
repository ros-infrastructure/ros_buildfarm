# Copyright 2013-2016 Open Source Robotics Foundation, Inc.
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

import logging
import os

import yaml

try:
    from urllib.parse import urljoin
except ImportError:
    from urlparse import urljoin

from .ci_build_file import CIBuildFile
from .doc_build_file import DocBuildFile
from .index import Index
from .loader import load_url
from .release_build_file import ReleaseBuildFile
from .source_build_file import SourceBuildFile

logger = logging.getLogger('ros_buildfarm.config')


def load_yaml(url):
    class SafeLoaderWithInclude(yaml.SafeLoader):

        def include(self, node):
            include_url = urljoin(url, self.construct_scalar(node))
            return load_yaml(include_url)

    SafeLoaderWithInclude.add_constructor('!include', SafeLoaderWithInclude.include)

    yaml_str = load_url(url)
    return yaml.load(yaml_str, SafeLoaderWithInclude)


def get_index(url):
    logger.debug("Load index from '%s'" % url)
    data = load_yaml(url)
    base_url = os.path.dirname(url)
    return Index(data, base_url)


def get_distribution_file(index, rosdistro_name, build_file):
    from rosdistro import get_distribution_files
    dist_files = get_distribution_files(index, rosdistro_name)
    dist_files = build_file.filter_distribution_files_by_tags(dist_files)
    while len(dist_files) > 1:
        dist_files[0].merge(dist_files[1])
        del dist_files[1]
    return dist_files[0] if dist_files else []


def get_ci_build_files(index, dist_name):
    data = _get_build_file_data(index, dist_name, 'ci_builds')
    build_files = {}
    for k, v in data.items():
        build_files[k] = CIBuildFile(k, v)
    return build_files


def get_release_build_files(index, dist_name):
    data = _get_build_file_data(index, dist_name, 'release_builds')
    build_files = {}
    for k, v in data.items():
        build_files[k] = ReleaseBuildFile(k, v)
    return build_files


def get_source_build_files(index, dist_name):
    data = _get_build_file_data(index, dist_name, 'source_builds')
    build_files = {}
    for k, v in data.items():
        build_files[k] = SourceBuildFile(k, v)
    return build_files


def get_doc_build_files(index, dist_name):
    data = _get_build_file_data(index, dist_name, 'doc_builds')
    build_files = {}
    for k, v in data.items():
        build_files[k] = DocBuildFile(k, v)
    return build_files


def get_global_doc_build_files(index):
    data = _load_build_file_data(index.doc_builds)
    build_files = {}
    for k, v in data.items():
        build_files[k] = DocBuildFile(k, v)
    return build_files


def _get_build_file_data(index, dist_name, type_):
    if dist_name not in index.distributions.keys():
        raise RuntimeError(
            "Unknown release: '{0}'. Valid release names are: {1}".format(
                dist_name,
                ', '.join(["'%s'" % d for d in index.distributions.keys()])))
    dist = index.distributions[dist_name]
    if type_ not in dist.keys():
        return {}
    entries = dist[type_]
    return _load_build_file_data(entries)


def _load_build_file_data(entries):
    def _load_yaml_data(url):
        logger.debug('Load file from "%s"' % url)
        return load_yaml(url)

    data = {}
    for k, v in entries.items():
        data[k] = _load_yaml_data(v)
    return data
