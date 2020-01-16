# Copyright 2015-2016 Open Source Robotics Foundation, Inc.
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

from collections import ChainMap
import os

import yaml


class RosdocIndex(object):

    def __init__(self, rosdoc_index_paths):  # noqa: D107
        self.forward_deps = self._read_folder(rosdoc_index_paths, 'deps')
        self.reverse_deps = {}
        self._build_reverse_deps()

        self.metapackage_deps = self._read_folder(
            rosdoc_index_paths, 'metapackage_deps')
        self.metapackage_index = {}

        self._build_metapackage_index()

        self.locations = self._read_folder(rosdoc_index_paths, 'locations')

        self.hashes = self._read_folder(rosdoc_index_paths, 'hashes')

    def get_recursive_dependencies(self, pkg_name):
        # since the dependencies available from the rosdoc_index are not in
        # sync the algorithm must handle circular dependencies gracefully
        recursive_deps = set([])
        pkg_names = set([pkg_name])
        while len(pkg_names) > 0:
            name = pkg_names.pop()
            if name not in self.forward_deps:
                continue
            deps = set(self.forward_deps[name])
            assert name not in deps
            # consider only new dependencies
            deps -= recursive_deps
            # add to set to be traversed
            pkg_names |= deps
            # add to recursive dependencies
            recursive_deps |= deps
        return recursive_deps

    def set_forward_deps(self, key, deps):
        self.forward_deps[key] = deps
        self._build_reverse_deps()

    def set_metapackage_deps(self, key, deps):
        self.metapackage_deps[key] = deps
        if deps is None:
            del self.metapackage_deps[key]
        self._build_metapackage_index()

    def write_modified_data(self, path, folder_names=None):
        all_folder_names = ['deps', 'metapackage_deps', 'locations', 'hashes']
        if folder_names is None:
            folder_names = all_folder_names

        for folder_name in folder_names:
            assert folder_name in all_folder_names

        # write only the added / modified entries
        if 'deps' in folder_names:
            self._write_folder(path, 'deps', self.forward_deps.maps[0])
        if 'metapackage_deps' in folder_names:
            self._write_folder(
                path, 'metapackage_deps', self.metapackage_deps.maps[0])
        if 'locations' in folder_names:
            self._write_folder(path, 'locations', self.locations.maps[0])
        if 'hashes' in folder_names:
            self._write_folder(path, 'hashes', self.hashes.maps[0])

    # turn a list of folders with files into a ChainMap
    def _read_folder(self, basepaths, folder_name):
        maps = [{}]  # the first dict will be used for added/modified entries
        for basepath in basepaths:
            data = {}
            path = os.path.join(basepath, folder_name)
            if os.path.exists(path):
                for key in os.listdir(path):
                    with open(os.path.join(path, key), 'r') as h:
                        data[key] = yaml.safe_load(h)
            maps.append(data)
        return ChainMap(*maps)

    # write a dict to files where is the filenames equal the keys
    def _write_folder(self, basepath, folder_name, data):
        path = os.path.join(basepath, folder_name)

        # ensure that thedirectory exists
        if not os.path.isdir(path):
            os.makedirs(path)

        for key, values in data.items():
            filename = os.path.join(path, key)
            if values is not None:
                with open(filename, 'w') as h:
                    yaml.safe_dump(values, h)
            elif os.path.exists(filename):
                os.remove(filename)

    def _build_metapackage_index(self):
        self.metapackage_index = {}
        for pkg_name, deps in self.metapackage_deps.items():
            for dep in deps or []:
                self.metapackage_index.setdefault(dep, []).append(pkg_name)

    def _build_reverse_deps(self):
        self.reverse_deps = {}
        for pkg_name, deps in self.forward_deps.items():
            for dep in deps or []:
                self.reverse_deps.setdefault(dep, []).append(pkg_name)
