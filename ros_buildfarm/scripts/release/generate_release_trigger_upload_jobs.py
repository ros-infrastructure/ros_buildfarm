# Copyright 2017 Open Source Robotics Foundation, Inc.
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

import argparse
import sys

from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_dry_run
from ros_buildfarm.common import JobValidationError
from ros_buildfarm.common import package_format_mapping
from ros_buildfarm.config import get_index
from ros_buildfarm.config import get_release_build_files
from ros_buildfarm.jenkins import configure_job
from ros_buildfarm.jenkins import connect
from ros_buildfarm.release_job import get_sync_packages_to_main_job_name
from ros_buildfarm.release_job import get_sync_packages_to_testing_job_name
from ros_buildfarm.templates import expand_template


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate the 'upload_main' and 'upload_testing' jobs.")
    add_argument_config_url(parser)
    add_argument_dry_run(parser)
    args = parser.parse_args(argv)

    template_name = 'release/trigger_upload_repo_job.xml.em'

    config = get_index(args.config_url)
    jenkins = connect(config.jenkins_url)

    for repo in ['main', 'testing']:
        job_name = 'upload_%s' % repo
        block_when_upstream_building = 'true'
        if repo == 'testing':
            block_when_upstream_building = 'false'
        job_config = expand_template(template_name, {
            'block_when_upstream_building': block_when_upstream_building,
            'sync_targets': sorted(get_sync_targets(config, repo)),
            'upstream_job_names': get_upstream_job_names(config, repo),
            'recipients': config.notify_emails})

        configure_job(jenkins, job_name, job_config, dry_run=args.dry_run)


def get_sync_targets(config, repo):
    targets = set()
    distributions = config.distributions.keys()
    for rosdistro in distributions:
        build_files = get_release_build_files(config, rosdistro)
        for build_file in build_files.values():
            for os_name in build_file.targets.keys():
                if os_name in ['debian', 'ubuntu']:
                    targets.add(repo)
                else:
                    targets.add(os_name + '-' + repo)
    return targets


def get_upstream_job_names(config, repo):
    distributions = config.distributions.keys()
    package_formats_per_rosdistro = {}
    for rosdistro in distributions:
        package_formats_per_rosdistro.setdefault(rosdistro, set())
        build_files = get_release_build_files(config, rosdistro)
        for build_file in build_files.values():
            for os_name in build_file.targets.keys():
                package_formats_per_rosdistro[rosdistro].add(
                    package_format_mapping[os_name])
    upstream_job_names = []
    if repo == 'main':
        for rosdistro, package_formats in package_formats_per_rosdistro.items():
            for package_format in package_formats:
                upstream_job_names.append(
                    get_sync_packages_to_main_job_name(rosdistro, package_format))
    elif repo == 'testing':
        for rosdistro in distributions:
            platforms = {}
            build_files = get_release_build_files(config, rosdistro)
            for build_file in build_files.values():
                for os_name in build_file.targets.keys():
                    platforms.setdefault(os_name, {})
                    for code_name, architectures in build_file.targets[os_name].items():
                        platforms[os_name].setdefault(code_name, set())
                        platforms[os_name][code_name].update(architectures.keys())

            for os_name, code_names in platforms.items():
                for code_name, architectures in code_names.items():
                    for arch in architectures:
                        upstream_job_names.append(
                            get_sync_packages_to_testing_job_name(
                                rosdistro, os_name, code_name, arch))
    else:
        raise JobValidationError("Unknown upstream jobs for job 'upload_{}'." % repo)
    for package_format in set(
        pf for pfs in package_formats_per_rosdistro.values() for pf in pfs
    ):
        if package_format == 'deb':
            upstream_job_names.append('import_upstream')
        else:
            upstream_job_names.append('import_upstream_' + package_format)
    return ','.join(sorted(upstream_job_names))


if __name__ == '__main__':
    sys.exit(main())
