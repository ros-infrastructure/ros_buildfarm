#!/usr/bin/env python3

import argparse
import copy
from datetime import datetime
import sys

from ros_buildfarm.argument import add_argument_config_url
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
        description="Generate the 'dashboard' job on Jenkins")
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    args = parser.parse_args(argv)

    config = get_index(args.config_url)
    job_config = get_job_config(args, config)

    jenkins = connect(config.jenkins_url)

    view = configure_view(jenkins, JENKINS_MANAGEMENT_VIEW)

    job_name = '%s_rosdistro_cache' % args.rosdistro_name
    configure_job(jenkins, job_name, job_config, view=view)


def get_job_config(args, config):
    template_name = 'misc/rosdistro_cache_job.xml.em'
    now = datetime.utcnow()
    now_str = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    apt_mirror_args, script_generating_key_files = \
        get_repositories_and_script_generating_key_files(config)

    job_data = copy.deepcopy(args.__dict__)
    job_data.update({
        'template_name': template_name,
        'now_str': now_str,

        'ros_buildfarm_url': get_repository_url('.'),

        'script_generating_key_files': script_generating_key_files,

        'rosdistro_index_url': config.rosdistro_index_url,

        'repository_args': apt_mirror_args,

        'notification_emails': config.notify_emails,
    })
    job_config = expand_template(template_name, job_data)
    return job_config


if __name__ == '__main__':
    main()
