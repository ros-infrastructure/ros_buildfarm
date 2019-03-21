#!/usr/bin/env python3

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

import argparse
import sys

from em import BANGPATH_OPT
from em import Hook
from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_build_tool
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_repository_name
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.common import get_devel_job_name
from ros_buildfarm.config import get_index as get_config_index
from ros_buildfarm.config import get_source_build_files
from ros_buildfarm.devel_job import configure_devel_job
from ros_buildfarm.templates import expand_template


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate a 'devel' script")
    add_argument_config_url(parser)
    add_argument_rosdistro_name(parser)
    add_argument_build_name(parser, 'source')
    add_argument_repository_name(parser)
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)
    add_argument_build_tool(parser)
    args = parser.parse_args(argv)

    # collect all template snippets of specific types
    class IncludeHook(Hook):

        def __init__(self):
            Hook.__init__(self)
            self.scms = []
            self.scripts = []

        def beforeInclude(self, *_, **kwargs):
            template_path = kwargs['file'].name
            if template_path.endswith('/snippet/scm.xml.em'):
                self.scms.append(
                    (kwargs['locals']['repo_spec'], kwargs['locals']['path']))
            if template_path.endswith('/snippet/builder_shell.xml.em'):
                script = kwargs['locals']['script']
                # reuse existing ros_buildfarm folder if it exists
                if 'Clone ros_buildfarm' in script:
                    lines = script.splitlines()
                    lines.insert(0, 'if [ ! -d "ros_buildfarm" ]; then')
                    lines += [
                        'else',
                        'echo "Using existing ros_buildfarm folder"',
                        'fi',
                    ]
                    script = '\n'.join(lines)
                if args.build_tool and ' --build-tool ' in script:
                    script = script.replace(
                        ' --build-tool catkin_make_isolated',
                        ' --build-tool ' + args.build_tool)
                self.scripts.append(script)

    hook = IncludeHook()
    from ros_buildfarm import templates
    templates.template_hooks = [hook]

    config = get_config_index(args.config_url)
    build_files = get_source_build_files(config, args.rosdistro_name)
    build_file = build_files[args.source_build_name]

    configure_devel_job(
        args.config_url, args.rosdistro_name, args.source_build_name,
        args.repository_name, args.os_name, args.os_code_name, args.arch,
        config=config, build_file=build_file, jenkins=False, views=False)

    templates.template_hooks = None

    devel_job_name = get_devel_job_name(
        args.rosdistro_name, args.source_build_name,
        args.repository_name, args.os_name, args.os_code_name, args.arch)

    value = expand_template(
        'devel/devel_script.sh.em', {
            'devel_job_name': devel_job_name,
            'scms': hook.scms,
            'scripts': hook.scripts,
            'build_tool': args.build_tool or build_file.build_tool},
        options={BANGPATH_OPT: False})
    value = value.replace('python3', sys.executable)
    print(value)


if __name__ == '__main__':
    sys.exit(main())
