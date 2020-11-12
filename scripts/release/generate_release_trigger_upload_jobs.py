#!/usr/bin/env python3

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
from ros_buildfarm.common import get_release_job_prefix
from ros_buildfarm.common import JobValidationError
from ros_buildfarm.config import get_index
from ros_buildfarm.config import get_release_build_files
from ros_buildfarm.jenkins import configure_job
from ros_buildfarm.jenkins import connect
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
            'repo': repo,
            'upstream_job_names': get_upstream_job_names(config, repo),
            'recipients': config.notify_emails})

        configure_job(jenkins, job_name, job_config, dry_run=args.dry_run)


def get_upstream_job_names(config, repo):
    distributions = config.distributions.keys()
    if repo == 'main':
        upstream_job_names = ['{0}_sync-packages-to-{1}'.format(
            get_release_job_prefix(rosdistro), repo) for rosdistro in distributions]
    elif repo == 'testing':
        upstream_job_names = []
        for rosdistro in distributions:
            architectures_by_code_name = {}
            build_files = get_release_build_files(config, rosdistro)
            for build_file in build_files.values():
                for os_name in build_file.targets.keys():
                    for code_name, architectures in build_file.targets[os_name].items():
                        architectures_by_code_name[code_name] = \
                            architectures_by_code_name.get(code_name, set()) | \
                            set(architectures.keys())

            for code_name, archs in architectures_by_code_name.items():
                for arch in archs:
                    upstream_job_names.append(
                        '{prefix}_sync-packages-to-{repo}_{code_name}_{arch}'.format(
                            prefix=get_release_job_prefix(rosdistro),
                            repo=repo,
                            code_name=code_name,
                            arch=arch))
    else:
        raise JobValidationError("Unknown upstream jobs for job 'upload_{}'." % repo)
    upstream_job_names.append('import_upstream')
    return ','.join(sorted(upstream_job_names))


if __name__ == '__main__':
    main()
