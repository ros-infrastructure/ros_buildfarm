#!/usr/bin/env python3

# Copyright 2019 Open Source Robotics Foundation, Inc.
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
import os
import sys

from em import BANGPATH_OPT
from em import Hook
from ros_buildfarm.argument import add_argument_arch
from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_build_tool
from ros_buildfarm.argument import add_argument_build_tool_args
from ros_buildfarm.argument import add_argument_build_tool_test_args
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import add_argument_os_code_name
from ros_buildfarm.argument import add_argument_os_name
from ros_buildfarm.argument import add_argument_package_selection_args
from ros_buildfarm.argument import add_argument_repos_file_urls
from ros_buildfarm.argument import add_argument_rosdistro_name
from ros_buildfarm.argument import add_argument_skip_cleanup
from ros_buildfarm.argument import add_argument_test_branch
from ros_buildfarm.argument import build_tool_args_epilog_action
from ros_buildfarm.argument import extract_multiple_remainders
from ros_buildfarm.ci_job import configure_ci_job
from ros_buildfarm.common import get_ci_job_name
from ros_buildfarm.config import get_ci_build_files
from ros_buildfarm.config import get_index as get_config_index
from ros_buildfarm.templates import expand_template


def main(argv=sys.argv[1:]):
    build_tool_args_helper = build_tool_args_epilog_action(
        'ci', get_ci_build_files)
    parser = argparse.ArgumentParser(
        description="Generate a 'CI' script",
        formatter_class=argparse.RawTextHelpFormatter)

    # Positional
    add_argument_config_url(parser, action=build_tool_args_helper)
    add_argument_rosdistro_name(parser, action=build_tool_args_helper)
    add_argument_build_name(parser, 'ci', action=build_tool_args_helper)
    add_argument_os_name(parser)
    add_argument_os_code_name(parser)
    add_argument_arch(parser)

    add_argument_build_tool(parser)
    a1 = add_argument_package_selection_args(parser)
    a2 = add_argument_build_tool_args(parser)
    a3 = add_argument_build_tool_test_args(parser)
    add_argument_repos_file_urls(parser)
    add_argument_skip_cleanup(parser)
    add_argument_test_branch(parser)
    parser.add_argument(
        '--underlay-source-path', nargs='*', metavar='DIR_NAME',
        help='Path to one or more install spaces to use as an underlay')

    remainder_args = extract_multiple_remainders(argv, (a1, a2, a3))
    args = parser.parse_args(argv)
    for k, v in remainder_args.items():
        setattr(args, k, v)

    # collect all template snippets of specific types
    class IncludeHook(Hook):

        def __init__(self):
            Hook.__init__(self)
            self.scms = []
            self.scripts = []
            self.parameters = {}

            if args.skip_cleanup:
                self.parameters['skip_cleanup'] = 'true'
            if args.repos_file_urls is not None:
                self.parameters['repos_file_urls'] = ' '.join(args.repos_file_urls)
            if args.test_branch is not None:
                self.parameters['test_branch'] = args.test_branch
            if args.package_selection_args is not None:
                self.parameters['package_selection_args'] = ' '.join(args.package_selection_args)
            if args.build_tool_args is not None:
                self.parameters['build_tool_args'] = ' '.join(args.build_tool_args)
            if args.build_tool_test_args is not None:
                self.parameters['build_tool_test_args'] = ' '.join(args.build_tool_test_args)

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
            if template_path.endswith('/snippet/property_parameters-definition.xml.em'):
                for parameter in reversed(kwargs['locals']['parameters']):
                    name = parameter['name']
                    value_type = parameter['type']
                    if value_type in ['string', 'text']:
                        default_value = parameter['default_value']
                    elif value_type == 'boolean':
                        default_value = 'true' if parameter.get(
                            'default_value', False) else 'false'
                    else:
                        continue

                    self.parameters.setdefault(name, default_value)

    hook = IncludeHook()
    from ros_buildfarm import templates
    templates.template_hooks = [hook]

    config = get_config_index(args.config_url)
    build_files = get_ci_build_files(config, args.rosdistro_name)
    build_file = build_files[args.ci_build_name]

    underlay_source_paths = [os.path.abspath(p) for p in args.underlay_source_path or []]

    configure_ci_job(
        args.config_url, args.rosdistro_name, args.ci_build_name,
        args.os_name, args.os_code_name, args.arch,
        config=config, build_file=build_file, jenkins=False, views=False,
        underlay_source_paths=underlay_source_paths)

    templates.template_hooks = None

    ci_job_name = get_ci_job_name(
        args.rosdistro_name, args.os_name,
        args.os_code_name, args.arch, 'script')

    value = expand_template(
        'ci/ci_script.sh.em', {
            'ci_job_name': ci_job_name,
            'scms': hook.scms,
            'scripts': hook.scripts,
            'build_tool': args.build_tool or build_file.build_tool,
            'parameters': hook.parameters},
        options={BANGPATH_OPT: False})
    value = value.replace('python3 ', sys.executable + ' ')
    print(value)


if __name__ == '__main__':
    sys.exit(main())
