#!/usr/bin/env python3

import argparse
from datetime import datetime
import sys

from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.config import get_index
from ros_buildfarm.jenkins import configure_job
from ros_buildfarm.jenkins import configure_view
from ros_buildfarm.jenkins import connect
from ros_buildfarm.jenkins import JENKINS_MANAGEMENT_VIEW
from ros_buildfarm.templates import expand_template


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate the 'dashboard' job on Jenkins")
    add_argument_config_url(parser)
    args = parser.parse_args(argv)

    config = get_index(args.config_url)
    job_config = get_job_config(config.notify_emails)

    jenkins = connect(config.jenkins_url)

    view = configure_view(jenkins, JENKINS_MANAGEMENT_VIEW)

    job_name = 'dashboard'
    configure_job(jenkins, job_name, job_config, view=view)


def get_job_config(notification_emails):
    template_name = 'dashboard_job.xml.em'
    now = datetime.utcnow()
    now_str = now.strftime('%Y-%m-%dT%H:%M:%SZ')

    job_data = {
        'template_name': template_name,
        'now_str': now_str,

        'notification_emails': notification_emails,
    }
    job_config = expand_template(template_name, job_data)
    return job_config


if __name__ == '__main__':
    main()
