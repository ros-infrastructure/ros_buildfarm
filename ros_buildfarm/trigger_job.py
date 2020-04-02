# Copyright 2014-2016 Open Source Robotics Foundation, Inc.
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


from ros_buildfarm.jenkins import connect
from ros_buildfarm.jenkins import invoke_job
from rosdistro import get_cached_distribution
from rosdistro import get_index

from .common import get_binarydeb_job_name
from .common import get_os_package_name
from .common import get_sourcedeb_job_name
from .common import Target
from .config import get_index as get_config_index
from .config import get_release_build_files
from .package_repo import get_package_repo_data
from .status_page import _strip_version_suffix
from .templates import expand_template


def trigger_release_jobs(
        config_url, rosdistro_name, release_build_name,
        missing_only, source_only, cache_dir, cause=None, groovy_script=None,
        not_failed_only=False):
    config = get_config_index(config_url)
    build_files = get_release_build_files(config, rosdistro_name)
    build_file = build_files[release_build_name]

    index = get_index(config.rosdistro_index_url)

    # get targets
    targets = []
    for os_name in sorted(build_file.targets.keys()):
        for os_code_name in sorted(build_file.targets[os_name].keys()):
            targets.append(Target(os_name, os_code_name, 'source'))
            if source_only:
                continue
            for arch in sorted(
                    build_file.targets[os_name][os_code_name].keys()):
                targets.append(Target(os_name, os_code_name, arch))
    print('The build file contains the following targets:')
    for os_name, os_code_name, arch in targets:
        print('  - %s %s %s' % (os_name, os_code_name, arch))

    dist_file = get_cached_distribution(index, rosdistro_name)
    if not dist_file:
        print('No distribution file matches the build file')
        return

    repo_data = None
    if missing_only:
        repo_data = get_package_repo_data(
            build_file.target_repository, targets, cache_dir)

    if groovy_script is None:
        jenkins = connect(config.jenkins_url)

    pkg_names = dist_file.release_packages.keys()
    pkg_names = build_file.filter_packages(pkg_names)

    triggered_jobs = []
    skipped_jobs = []
    for pkg_name in sorted(pkg_names):
        pkg = dist_file.release_packages[pkg_name]
        repo_name = pkg.repository_name
        repo = dist_file.repositories[repo_name]
        if not repo.release_repository:
            print(("  Skipping package '%s' in repository '%s': no release " +
                   "section") % (pkg_name, repo_name))
            continue
        if not repo.release_repository.version:
            print(("  Skipping package '%s' in repository '%s': no release " +
                   "version") % (pkg_name, repo_name))
            continue
        pkg_version = repo.release_repository.version

        debian_package_name = get_os_package_name(rosdistro_name, pkg_name)

        for target in targets:
            job_name = get_sourcedeb_job_name(
                rosdistro_name, release_build_name,
                pkg_name, target.os_name, target.os_code_name)
            if target.arch != 'source':
                # binary job can be skipped if source job was triggered
                if job_name in triggered_jobs:
                    print(("  Skipping binary jobs of '%s' since the source " +
                           "job was triggered") % job_name)
                    continue
                job_name = get_binarydeb_job_name(
                    rosdistro_name, release_build_name,
                    pkg_name, target.os_name, target.os_code_name, target.arch)

            if repo_data:
                # check if artifact is missing
                repo_index = repo_data[target]
                if debian_package_name in repo_index:
                    version = repo_index[debian_package_name].version
                    version = _strip_version_suffix(version)
                    if version == pkg_version:
                        print(("  Skipping job '%s' since the artifact is " +
                               "already up-to-date") % job_name)
                        continue

            if groovy_script is None:
                success = invoke_job(jenkins, job_name, cause=cause)
            else:
                success = True
            if success:
                triggered_jobs.append(job_name)
            else:
                skipped_jobs.append(job_name)

    if groovy_script is None:
        print('Triggered %d jobs, skipped %d jobs.' %
              (len(triggered_jobs), len(skipped_jobs)))
    else:
        print("Writing groovy script '%s' to trigger %d jobs" %
              (groovy_script, len(triggered_jobs)))
        data = {
            'job_names': triggered_jobs,
            'not_failed_only': not_failed_only,
        }
        content = expand_template('release/trigger_jobs.groovy.em', data)
        with open(groovy_script, 'w') as h:
            h.write(content)
