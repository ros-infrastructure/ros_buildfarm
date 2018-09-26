# Copyright 2018 Open Source Robotics Foundation, Inc.
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

from .build_file import BuildFile


class CIBuildFile(BuildFile):

    _type = 'ci-build'

    def __init__(self, name, data):
        assert 'type' in data, "Expected file type is '%s'" % \
            CIBuildFile._type
        assert data['type'] == CIBuildFile._type, \
            "Expected file type is '%s', not '%s'" % \
            (CIBuildFile._type, data['type'])

        assert 'version' in data, \
            "Source build file for '%s' lacks required version information" % \
            self.name
        assert int(data['version']) in [1], \
            ("Unable to handle '%s' format version '%d', please update " +
             "rosdistro (e.g. on Ubuntu/Debian use: sudo apt update && " +
             "sudo apt install --only-upgrade python-rosdistro)") % \
            (CIBuildFile._type, int(data['version']))
        self.version = int(data['version'])

        super(CIBuildFile, self).__init__(name, data)

        self.build_ignore = []
        if 'build_ignore' in data:
            self.build_ignore = data['build_ignore']
            assert isinstance(self.build_ignore, list)

        self.jenkins_job_label = None
        if 'jenkins_job_label' in data:
            self.jenkins_job_label = data['jenkins_job_label']
        self.jenkins_job_timeout = None
        if 'jenkins_job_timeout' in data:
            self.jenkins_job_timeout = int(data['jenkins_job_timeout'])

        self.repos_files = []
        if 'repos_files' in data:
            self.repos_files = data['repos_files']
            assert isinstance(self.repos_files, list)

        self.skip_rosdep_keys = []
        if 'skip_rosdep_keys' in data:
            self.skip_rosdep_keys = data['skip_rosdep_keys']
            assert isinstance(self.skip_rosdep_keys, list)

        self.custom_rosdep_urls = []
        if '_config' in data['targets']:
            if 'custom_rosdep_urls' in data['targets']['_config']:
                self.custom_rosdep_urls = \
                    data['targets']['_config']['custom_rosdep_urls']
                assert isinstance(self.custom_rosdep_urls, list)

        self.collate_test_stats = bool(data.get('collate_test_stats', False))
