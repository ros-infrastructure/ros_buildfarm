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

from .build_file import BuildFile


class ReleaseBuildFile(BuildFile):

    _type = 'release-build'

    def __init__(self, name, data):  # noqa: D107
        assert 'type' in data, \
            "Expected file type is '%s'" % ReleaseBuildFile._type
        assert data['type'] == ReleaseBuildFile._type, \
            "Expected file type is '%s', not '%s'" % \
            (ReleaseBuildFile._type, data['type'])

        assert 'version' in data, \
            ("Release build file for '%s' lacks required version " +
             "information") % self.name
        assert int(data['version']) in [1, 2], \
            ("Unable to handle '%s' format version '%d', please update " +
             "rosdistro (e.g. on Ubuntu/Debian use: sudo apt update && " +
             "sudo apt install --only-upgrade python-rosdistro)") % \
            (ReleaseBuildFile._type, int(data['version']))
        self.version = int(data['version'])

        super(ReleaseBuildFile, self).__init__(name, data)

        assert len(self.targets) > 0

        self.abi_incompatibility_assumed = None
        if 'abi_incompatibility_assumed' in data:
            self.abi_incompatibility_assumed = \
                bool(data['abi_incompatibility_assumed'])

        self.jenkins_binary_job_label = None
        if 'jenkins_binary_job_label' in data:
            self.jenkins_binary_job_label = data['jenkins_binary_job_label']
        self.jenkins_binary_job_priority = None
        if 'jenkins_binary_job_priority' in data:
            self.jenkins_binary_job_priority = \
                int(data['jenkins_binary_job_priority'])
        self.jenkins_binary_job_timeout = None
        if 'jenkins_binary_job_timeout' in data:
            self.jenkins_binary_job_timeout = \
                int(data['jenkins_binary_job_timeout'])

        self.jenkins_source_job_label = None
        if 'jenkins_source_job_label' in data:
            self.jenkins_source_job_label = data['jenkins_source_job_label']
        self.jenkins_source_job_priority = None
        if 'jenkins_source_job_priority' in data:
            self.jenkins_source_job_priority = \
                int(data['jenkins_source_job_priority'])
        self.jenkins_source_job_timeout = None
        if 'jenkins_source_job_timeout' in data:
            self.jenkins_source_job_timeout = \
                int(data['jenkins_source_job_timeout'])

        self.package_whitelist = []
        if 'package_whitelist' in data and data['package_whitelist']:
            self.package_whitelist = data['package_whitelist']
            assert isinstance(self.package_whitelist, list)
        self.package_blacklist = []
        if 'package_blacklist' in data and data['package_blacklist']:
            self.package_blacklist = data['package_blacklist']
            assert isinstance(self.package_blacklist, list)
        self.package_ignore_list = []
        if 'package_ignore_list' in data and data['package_ignore_list']:
            self.package_ignore_list = data['package_ignore_list']
            assert isinstance(self.package_ignore_list, list)
        self.skip_ignored_packages = None
        if 'skip_ignored_packages' in data:
            self.skip_ignored_packages = \
                bool(data['skip_ignored_packages'])

        self.sync_package_count = None
        self.sync_packages = []
        if 'sync' in data:
            if 'package_count' in data['sync']:
                self.sync_package_count = int(data['sync']['package_count'])
            if 'packages' in data['sync'] and data['sync']['packages']:
                self.sync_packages = data['sync']['packages']
                assert isinstance(self.sync_packages, list)

        self.target_queue = None
        if 'target_queue' in data:
            self.target_queue = str(data['target_queue'])
        assert 'target_repository' in data
        self.target_repository = data['target_repository']

        assert 'upload_credential_id' in data
        self.upload_credential_id = data['upload_credential_id']

        self.upload_destination_credential_id = None
        if 'upload_destination_credential_id' in data:
            self.upload_destination_credential_id = data['upload_destination_credential_id']

    def filter_packages(self, package_names):
        res = set(package_names)
        if self.package_whitelist:
            res &= set(self.package_whitelist)
        res -= set(self.package_blacklist)
        res -= set(self.package_ignore_list)
        return res
