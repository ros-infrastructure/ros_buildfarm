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


class SourceBuildFile(BuildFile):

    _type = 'source-build'

    def __init__(self, name, data):  # noqa: D107
        assert 'type' in data, "Expected file type is '%s'" % \
            SourceBuildFile._type
        assert data['type'] == SourceBuildFile._type, \
            "Expected file type is '%s', not '%s'" % \
            (SourceBuildFile._type, data['type'])

        assert 'version' in data, \
            "Source build file for '%s' lacks required version information" % \
            self.name
        assert int(data['version']) in [1, 2, 3], \
            ("Unable to handle '%s' format version '%d', please update " +
             "rosdistro (e.g. on Ubuntu/Debian use: sudo apt update && " +
             "sudo apt install --only-upgrade python-rosdistro)") % \
            (SourceBuildFile._type, int(data['version']))
        self.version = int(data['version'])

        super(SourceBuildFile, self).__init__(name, data)

        assert len(self.targets) > 0

        self.jenkins_commit_job_priority = None
        if 'jenkins_commit_job_priority' in data:
            self.jenkins_commit_job_priority = \
                int(data['jenkins_commit_job_priority'])
        self.jenkins_pull_request_job_priority = None
        if 'jenkins_pull_request_job_priority' in data:
            self.jenkins_pull_request_job_priority = \
                int(data['jenkins_pull_request_job_priority'])

        self.jenkins_job_label = None
        if 'jenkins_job_label' in data:
            self.jenkins_job_label = data['jenkins_job_label']
        self.jenkins_job_timeout = None
        if 'jenkins_job_timeout' in data:
            self.jenkins_job_timeout = int(data['jenkins_job_timeout'])

        self.build_tool = data.get('build_tool', 'catkin_make_isolated')
        assert self.build_tool in ('catkin_make_isolated', 'colcon')

        self.build_tool_args = None
        if 'build_tool_args' in data:
            self.build_tool_args = data['build_tool_args']

        self.build_tool_test_args = None
        if 'build_tool_test_args' in data:
            self.build_tool_test_args = data['build_tool_test_args']

        self.notify_committers = None
        self.notify_compiler_warnings = False
        self.notify_pull_requests = False
        if 'notifications' in data:
            if 'committers' in data['notifications']:
                self.notify_committers = \
                    bool(data['notifications']['committers'])
            if 'compiler_warnings' in data['notifications']:
                self.notify_compiler_warnings = \
                    bool(data['notifications']['compiler_warnings'])
            if 'pull_requests' in data['notifications']:
                self.notify_pull_requests = \
                    bool(data['notifications']['pull_requests'])

        self.repository_blacklist = []
        if 'repository_blacklist' in data:
            self.repository_blacklist = data['repository_blacklist']
            assert isinstance(self.repository_blacklist, list)
        self.repository_whitelist = []
        if 'repository_whitelist' in data:
            self.repository_whitelist = data['repository_whitelist']
            assert isinstance(self.repository_whitelist, list)
        self.skip_ignored_repositories = None
        if 'skip_ignored_repositories' in data:
            self.skip_ignored_repositories = \
                bool(data['skip_ignored_repositories'])

        self.custom_rosdep_urls = []
        if '_config' in data['targets']:
            if 'custom_rosdep_urls' in data['targets']['_config']:
                self.custom_rosdep_urls = \
                    data['targets']['_config']['custom_rosdep_urls']
                assert isinstance(self.custom_rosdep_urls, list)

        self.test_commits_default = False
        self.test_commits_force = None
        if 'test_commits' in data:
            if 'default' in data['test_commits']:
                self.test_commits_default = bool(
                    data['test_commits']['default'])
            if 'force' in data['test_commits']:
                self.test_commits_force = bool(
                    data['test_commits']['force'])

        self.test_pull_requests_default = False
        self.test_pull_requests_force = None
        if 'test_pull_requests' in data:
            if 'default' in data['test_pull_requests']:
                self.test_pull_requests_default = bool(
                    data['test_pull_requests']['default'])
            if 'force' in data['test_pull_requests']:
                self.test_pull_requests_force = bool(
                    data['test_pull_requests']['force'])

        self.test_abi_default = False
        self.test_abi_force = None
        if 'test_abi' in data:
            if 'default' in data['test_abi']:
                self.test_abi_default = bool(
                    data['test_abi']['default'])
            if 'force' in data['test_abi']:
                self.test_abi_force = bool(
                    data['test_abi']['force'])

        self.tests_require_gpu_default = False
        if 'tests_require_gpu' in data:
            if 'default' in data['tests_require_gpu']:
                self.tests_require_gpu_default = bool(
                    data['tests_require_gpu']['default'])

        self.collate_test_stats = bool(data.get('collate_test_stats', False))

        self.benchmark_patterns = []
        if 'benchmark_patterns' in data:
            self.benchmark_patterns = data['benchmark_patterns']
            assert isinstance(self.benchmark_patterns, list)
            assert all(isinstance(pattern, str) for pattern in self.benchmark_patterns)

        self.benchmark_schema = None
        if 'benchmark_schema' in data:
            self.benchmark_schema = data['benchmark_schema'].strip()
            self._assert_valid_benchmark_schema()
            assert self.benchmark_patterns, \
                "The 'benchmark_patterns' value is required when using 'benchmark_schema'"

    def filter_repositories(self, repository_names):
        res = set(repository_names)
        if self.repository_whitelist:
            res &= set(self.repository_whitelist)
        res -= set(self.repository_blacklist)
        return res
