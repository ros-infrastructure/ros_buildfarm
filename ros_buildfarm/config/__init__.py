# Software License Agreement (BSD License)
#
# Copyright (c) 2013, Open Source Robotics Foundation, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Open Source Robotics Foundation, Inc. nor
#    the names of its contributors may be used to endorse or promote
#    products derived from this software without specific prior
#    written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from __future__ import print_function

import logging
import os
import yaml

logger = logging.getLogger('ros_buildfarm.config')

from .doc_build_file import DocBuildFile
from .index import Index
from .loader import load_url
from .release_build_file import ReleaseBuildFile
from .source_build_file import SourceBuildFile


def get_index(url):
    logger.debug("Load index from '%s'" % url)
    yaml_str = load_url(url)
    data = yaml.load(yaml_str)
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
        yaml_str = load_url(url)
        return yaml.load(yaml_str)

    data = {}
    for k, v in entries.items():
        data[k] = _load_yaml_data(v)
    return data
