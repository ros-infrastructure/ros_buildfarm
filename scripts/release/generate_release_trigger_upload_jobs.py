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
from ros_buildfarm.config import get_index
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
    distributions = config.distributions.keys()

    for repo in ['main', 'testing']:
        job_name = 'upload_%s' % repo
        block_when_upstream_building = 'true'
        if repo == 'testing':
            block_when_upstream_building = 'false'
        upstream_job_names = ['{0}_sync-packages-to-{1}'.format(
            get_release_job_prefix(rosdistro), repo) for rosdistro in distributions]
        upstream_job_names = ', '.join(sorted(upstream_job_names))
        job_config = expand_template(template_name, {
            'block_when_upstream_building': block_when_upstream_building,
            'repo': repo,
            'upstream_job_names': upstream_job_names})

        configure_job(jenkins, job_name, job_config, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
