#!/usr/bin/env python3

import argparse
import copy
from datetime import datetime
import sys

from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_debian_repository_urls
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.common import \
    get_repositories_and_script_generating_key_files
from ros_buildfarm.config import get_index
from ros_buildfarm.git import get_repository_url
from ros_buildfarm.jenkins import configure_job
from ros_buildfarm.jenkins import configure_view
from ros_buildfarm.jenkins import connect
from ros_buildfarm.jenkins import JENKINS_MANAGEMENT_VIEW
from ros_buildfarm.templates import expand_template


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate the 'release_status_page' job on Jenkins")
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'release')
    args = parser.parse_args(argv)

    config = get_index(args.config_url)
    job_config = get_job_config(args, config)

    jenkins = connect(config.jenkins_url)

    view = configure_view(jenkins, JENKINS_MANAGEMENT_VIEW)

    job_name = '%s_%s_release-status-page' % \
        (args.rosdistro_name, args.release_build_name)
    configure_job(jenkins, job_name, job_config, view=view)


def get_job_config(args, config):
    template_name = 'status/release_status_page_job.xml.em'
    now = datetime.utcnow()
    now_str = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    repository_args, script_generating_key_files = \
        get_repositories_and_script_generating_key_files(config)

    job_data = copy.deepcopy(args.__dict__)
    job_data.update({
        'template_name': template_name,
        'now_str': now_str,

        'ros_buildfarm_url': get_repository_url(),

        'script_generating_key_files': script_generating_key_files,

        'rosdistro_index_url': config.rosdistro_index_url,

        'repository_args': repository_args,

        'notification_emails': config.notify_emails,
    })
    job_config = expand_template(template_name, job_data)
    return job_config


if __name__ == '__main__':
    main()
