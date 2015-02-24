#!/usr/bin/env python3

import argparse
from em import BANGPATH_OPT
from em import Hook
import sys

from ros_buildfarm import templates
from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_force
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_repository_name
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.common import get_doc_job_name
from ros_buildfarm.doc_job import configure_doc_job
from ros_buildfarm.templates import expand_template


def main(argv=sys.argv[1:]):
    global templates
    parser = argparse.ArgumentParser(
        description="Generate a 'doc' script")
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'doc')
    add_argument_repository_name(parser)
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)
    add_argument_force(parser)
    args = parser.parse_args(argv)

    # collect all template snippets of specific types
    class IncludeHook(Hook):

        def __init__(self):
            super(IncludeHook, self).__init__()
            self.scms = []
            self.scripts = []

        def beforeInclude(self, *args, **kwargs):
            template_path = kwargs['file'].name
            if template_path.endswith('/snippet/scm.xml.em'):
                self.scms.append(
                    (kwargs['locals']['repo_spec'], kwargs['locals']['path']))
            if template_path.endswith('/snippet/builder_shell.xml.em'):
                self.scripts.append(kwargs['locals']['script'])

    hook = IncludeHook()
    templates.template_hooks = [hook]

    configure_doc_job(
        args.config_url, args.rosdistro_name, args.doc_build_name,
        args.repository_name, args.os_name, args.os_code_name, args.arch,
        jenkins=False, views=[])

    templates.template_hooks = None
    scripts = hook.scripts

    doc_job_name = get_doc_job_name(
        args.rosdistro_name, args.doc_build_name, args.repository_name,
        args.os_name, args.os_code_name, args .arch)

    # set force flag
    force_flag = '$force'
    for i, script in enumerate(scripts):
        offset = script.find(force_flag)
        if offset != -1:
            script = script[:offset] + ('true' if args.force else 'false') + \
                script[offset + len(force_flag):]
            scripts[i] = script
            break

    # remove rsync from server
    rsync_cmd = 'rsync'
    for i, script in enumerate(scripts):
        offset = script.find(rsync_cmd)
        if offset != -1:
            del scripts[i]
            break

    # remove rsync back to server
    cmd_part = '--delete'
    for i, script in enumerate(scripts):
        offset = script.find(cmd_part)
        if offset != -1:
            del scripts[i]
            break

    value = expand_template(
        'doc/doc_script.sh.em', {
            'doc_job_name': doc_job_name,
            'scms': hook.scms,
            'scripts': scripts},
        options={BANGPATH_OPT: False})
    print(value)


if __name__ == '__main__':
    sys.exit(main())
