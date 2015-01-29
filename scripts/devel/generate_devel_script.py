#!/usr/bin/env python3

import argparse
from em import BANGPATH_OPT
from em import Hook
import sys

from ros_buildfarm import templates
from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_repository_name
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.common import get_devel_job_name
from ros_buildfarm.devel_job import configure_devel_job
from ros_buildfarm.templates import expand_template


def main(argv=sys.argv[1:]):
    global templates
    parser = argparse.ArgumentParser(
        description="Generate a 'devel' script")
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'source')
    add_argument_repository_name(parser)
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)
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

    configure_devel_job(
        args.config_url, args.rosdistro_name, args.source_build_name,
        args.repository_name, args.os_name, args.os_code_name, args.arch,
        jenkins=False, views=False)

    templates.template_hooks = None

    devel_job_name = get_devel_job_name(
        args.rosdistro_name, args.source_build_name,
        args.repository_name, args.os_name, args.os_code_name, args.arch)

    value = expand_template(
        'devel/devel_script.sh.em', {
            'devel_job_name': devel_job_name,
            'scms': hook.scms,
            'scripts': hook.scripts},
        options={BANGPATH_OPT: False})
    print(value)


if __name__ == '__main__':
    sys.exit(main())
