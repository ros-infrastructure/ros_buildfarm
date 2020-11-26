# Copyright 2013-2015 Open Source Robotics Foundation, Inc.
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

import json
from xml.etree import ElementTree

from ros_buildfarm.common import Target


class BuildFile(object):

    def __init__(self, name, data):  # noqa: D107
        self.name = name

        self.build_environment_variables = None
        if 'build_environment_variables' in data:
            self.build_environment_variables = \
                data['build_environment_variables']
            assert(isinstance(self.build_environment_variables, dict))

        self.notify_emails = []
        self.notify_maintainers = None
        if 'notifications' in data:
            if 'emails' in data['notifications']:
                self.notify_emails = data['notifications']['emails']
                assert isinstance(self.notify_emails, list)
            if 'maintainers' in data['notifications'] and \
                    data['notifications']['maintainers']:
                self.notify_maintainers = True
        self.project_authorization_xml = None
        if 'project_authorization_xml' in data:
            self.project_authorization_xml = data['project_authorization_xml']

        self.repository_keys = []
        self.repository_urls = []
        if 'repositories' in data:
            if 'keys' in data['repositories']:
                self.repository_keys = data['repositories']['keys']
                assert isinstance(self.repository_keys, list)
            if 'urls' in data['repositories']:
                self.repository_urls = data['repositories']['urls']
                assert isinstance(self.repository_urls, list)
            assert len(self.repository_keys) == len(self.repository_urls)

        self.tag_whitelist = []
        self.tag_blacklist = []
        if 'tag_whitelist' in data:
            self.tag_whitelist = data['tag_whitelist']
            assert isinstance(self.tag_whitelist, list)
        if 'tag_blacklist' in data:
            self.tag_blacklist = data['tag_blacklist']
            assert isinstance(self.tag_blacklist, list)

        self.targets = {}
        for os_name in data.get('targets', {}).keys():
            if os_name == '_config':
                continue
            self.targets[os_name] = {}
            for os_code_name in data['targets'][os_name].keys():
                self.targets[os_name][os_code_name] = {}
                for arch in data['targets'][os_name][os_code_name].keys():
                    self.targets[os_name][os_code_name][arch] = \
                        data['targets'][os_name][os_code_name][arch]

        self.shared_ccache = False
        if 'shared_ccache' in data:
            self.shared_ccache = bool(data['shared_ccache'])

    def filter_distribution_files_by_tags(self, dist_files):
        res = []

        def match_distribution_file_tags(tags, whitelist, blacklist):
            # check if any tag matches the blacklist
            for tag in blacklist:
                if tag in tags:
                    return False
            # check if any tag matches the whitelist
            if whitelist:
                for tag in whitelist:
                    if tag in tags:
                        return True
            # if no tag matched any of the lists
            # the result depends on if a whitelist was specified
            return not whitelist

        for dist_file in dist_files:
            if match_distribution_file_tags(
                    dist_file.tags, self.tag_whitelist, self.tag_blacklist):
                res.append(dist_file)

        return res

    def get_targets_list(self):
        target_list = []
        for os_name, os_name_v in self.targets.items():
            if os_name == '_config':
                continue
            for os_code_name, os_code_name_v in os_name_v.items():
                for arch in os_code_name_v.keys():
                    target_list.append(Target(os_name, os_code_name, arch))
        return target_list

    def _assert_valid_benchmark_schema(self):
        assert isinstance(self.benchmark_schema, str)
        if self.benchmark_schema.startswith('<'):
            try:
                ElementTree.fromstring(self.benchmark_schema)
            except ElementTree.ParseError as e:
                assert False, "The 'benchmark_schema' value contains invalid XML: " + str(e)
        else:
            try:
                json.loads(self.benchmark_schema)
            except json.decoder.JSONDecodeError as e:
                assert False, "The 'benchmark_schema' value contains invalid JSON: " + str(e)
