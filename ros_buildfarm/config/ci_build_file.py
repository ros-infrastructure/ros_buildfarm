# Copyright 2019 Open Source Robotics Foundation, Inc.
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
            "Unable to handle '%s' format version '%d'." % \
            (CIBuildFile._type, int(data['version']))
        self.version = int(data['version'])

        super(CIBuildFile, self).__init__(name, data)

        self.build_tool = data.get('build_tool', 'colcon')
        assert self.build_tool in ('catkin_make_isolated', 'colcon')

        self.build_tool_args = None
        if 'build_tool_args' in data:
            self.build_tool_args = data['build_tool_args']

        self.install_packages = []
        if 'install_packages' in data:
            self.install_packages = data['install_packages']
            assert isinstance(self.install_packages, list)

        self.jenkins_job_label = None
        if 'jenkins_job_label' in data:
            self.jenkins_job_label = data['jenkins_job_label']
        self.jenkins_job_priority = None
        if 'jenkins_job_priority' in data:
            self.jenkins_job_priority = int(data['jenkins_job_priority'])
        self.jenkins_job_schedule = None
        if 'jenkins_job_schedule' in data:
            self.jenkins_job_schedule = data['jenkins_job_schedule']
        self.jenkins_job_timeout = None
        if 'jenkins_job_timeout' in data:
            self.jenkins_job_timeout = int(data['jenkins_job_timeout'])

        self.package_selection_args = None
        if 'package_selection_args' in data:
            self.package_selection_args = data['package_selection_args']

        self.repos_files = []
        if 'repos_files' in data:
            self.repos_files = data['repos_files']
            assert isinstance(self.repos_files, list)

        self.skip_rosdep_keys = []
        if 'skip_rosdep_keys' in data:
            self.skip_rosdep_keys = data['skip_rosdep_keys']
            assert isinstance(self.skip_rosdep_keys, list)

        self.test_branch = None
        if 'test_branch' in data:
            self.test_branch = data['test_branch']

        self.underlay_from_ci_jobs = []
        if 'underlay_from_ci_jobs' in data:
            self.underlay_from_ci_jobs = data['underlay_from_ci_jobs']
            assert isinstance(self.underlay_from_ci_jobs, list)
