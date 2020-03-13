#!/usr/bin/env python3

# Copyright 2015-2016 Open Source Robotics Foundation, Inc.
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

from __future__ import print_function

import argparse
import copy
import os
import re
import subprocess
import sys
import time

from apt import Cache
from catkin_pkg.packages import find_packages
from ros_buildfarm.argument import add_argument_build_name
from ros_buildfarm.argument import add_argument_build_tool
from ros_buildfarm.argument import add_argument_config_url
from ros_buildfarm.argument import \
    add_argument_distribution_repository_key_files
from ros_buildfarm.argument import add_argument_distribution_repository_urls
from ros_buildfarm.argument import add_argument_dockerfile_dir
from ros_buildfarm.argument import add_argument_force
from ros_buildfarm.argument import add_argument_output_dir
from ros_buildfarm.argument import add_argument_repository_name
from ros_buildfarm.argument import add_argument_vcs_information
from ros_buildfarm.common import find_executable
from ros_buildfarm.common import get_binary_package_versions
from ros_buildfarm.common import get_devel_job_urls
from ros_buildfarm.common import get_distribution_repository_keys
from ros_buildfarm.common import get_doc_job_url
from ros_buildfarm.common import get_os_package_name
from ros_buildfarm.common import get_package_condition_context
from ros_buildfarm.common import get_release_job_urls
from ros_buildfarm.common import get_user_id
from ros_buildfarm.common import Scope
from ros_buildfarm.common import topological_order_packages
from ros_buildfarm.config import get_distribution_file as \
    get_distribution_file_matching_build_file
from ros_buildfarm.config import get_doc_build_files
from ros_buildfarm.config import get_index as get_config_index
from ros_buildfarm.config import get_release_build_files
from ros_buildfarm.config import get_source_build_files
from ros_buildfarm.git import get_hash as get_git_hash
from ros_buildfarm.rosdoc_index import RosdocIndex
from ros_buildfarm.rosdoc_lite import get_generator_output_folders
from ros_buildfarm.templates import create_dockerfile
from ros_buildfarm.templates import expand_template
from rosdep2 import create_default_installer_context
from rosdep2.catkin_support import get_catkin_view
from rosdep2.catkin_support import resolve_for_os
from rosdistro import get_distribution_file
from rosdistro import get_index
import yaml


def main(argv=sys.argv[1:]):
    parser = argparse.ArgumentParser(
        description="Generate a 'Dockerfile' for the doc job")
    add_argument_config_url(parser)
    parser.add_argument(
        '--rosdistro-name',
        required=True,
        help='The name of the ROS distro to identify the setup file to be '
             'sourced')
    add_argument_build_name(parser, 'doc')
    parser.add_argument(
        '--workspace-root',
        required=True,
        help='The root path of the workspace to compile')
    parser.add_argument(
        '--rosdoc-lite-dir',
        required=True,
        help='The root path of the rosdoc_lite repository')
    parser.add_argument(
        '--catkin-sphinx-dir',
        required=True,
        help='The root path of the catkin-sphinx repository')
    parser.add_argument(
        '--rosdoc-index-dir',
        required=True,
        help='The root path of the rosdoc_index folder')
    add_argument_repository_name(parser)
    parser.add_argument(
        '--os-name',
        required=True,
        help="The OS name (e.g. 'ubuntu')")
    parser.add_argument(
        '--os-code-name',
        required=True,
        help="The OS code name (e.g. 'xenial')")
    parser.add_argument(
        '--arch',
        required=True,
        help="The architecture (e.g. 'amd64')")
    add_argument_build_tool(parser, required=True)
    add_argument_vcs_information(parser)
    add_argument_distribution_repository_urls(parser)
    add_argument_distribution_repository_key_files(parser)
    add_argument_force(parser)
    add_argument_output_dir(parser, required=True)
    add_argument_dockerfile_dir(parser)
    args = parser.parse_args(argv)

    config = get_config_index(args.config_url)
    index = get_index(config.rosdistro_index_url)

    condition_context = get_package_condition_context(index, args.rosdistro_name)

    with Scope('SUBSECTION', 'packages'):
        # find packages in workspace
        source_space = os.path.join(args.workspace_root, 'src')
        print("Crawling for packages in workspace '%s'" % source_space)
        pkgs = find_packages(source_space)

        for pkg in pkgs.values():
            pkg.evaluate_conditions(condition_context)

        pkg_names = [pkg.name for pkg in pkgs.values()]
        print('Found the following packages:')
        for pkg_name in sorted(pkg_names):
            print('  -', pkg_name)

        maintainer_emails = set([])
        for pkg in pkgs.values():
            for m in pkg.maintainers:
                maintainer_emails.add(m.email)
        if maintainer_emails:
            print('Package maintainer emails: %s' %
                  ' '.join(sorted(maintainer_emails)))

    rosdoc_index = RosdocIndex(
        [os.path.join(args.rosdoc_index_dir, args.rosdistro_name)])

    vcs_type, vcs_version, vcs_url = args.vcs_info.split(' ', 2)

    with Scope('SUBSECTION', 'determine need to run documentation generation'):
        # compare hashes to determine if documentation needs to be regenerated
        current_hashes = {}
        current_hashes['ros_buildfarm'] = 2  # increase to retrigger doc jobs
        current_hashes['rosdoc_lite'] = get_git_hash(args.rosdoc_lite_dir)
        current_hashes['catkin-sphinx'] = get_git_hash(args.catkin_sphinx_dir)
        repo_dir = os.path.join(
            args.workspace_root, 'src', args.repository_name)
        current_hashes[args.repository_name] = get_hash(repo_dir)
        print('Current repository hashes: %s' % current_hashes)
        tag_index_hashes = rosdoc_index.hashes.get(args.repository_name, {})
        print('Stored repository hashes: %s' % tag_index_hashes)
        skip_doc_generation = current_hashes == tag_index_hashes

    if skip_doc_generation:
        print('No changes to the source repository or any tooling repository')

        if not args.force:
            print('Skipping generation of documentation')

            # create stamp files
            print('Creating marker files to identify that documentation is ' +
                  'up-to-date')
            create_stamp_files(pkg_names, os.path.join(args.output_dir, 'api'))

            # check if any entry needs to be updated
            print('Creating update manifest.yaml files')
            for pkg_name in pkg_names:
                # update manifest.yaml files
                current_manifest_yaml_file = os.path.join(
                    args.rosdoc_index_dir, args.rosdistro_name, 'api', pkg_name,
                    'manifest.yaml')
                if not os.path.exists(current_manifest_yaml_file):
                    print('- %s: skipping no manifest.yaml yet' % pkg_name)
                    continue
                with open(current_manifest_yaml_file, 'r') as h:
                    remote_data = yaml.safe_load(h)
                data = copy.deepcopy(remote_data)

                data['vcs'] = vcs_type
                data['vcs_uri'] = vcs_url
                data['vcs_version'] = vcs_version

                data['depends_on'] = sorted(rosdoc_index.reverse_deps.get(pkg_name, []))

                if data == remote_data:
                    print('- %s: skipping same data' % pkg_name)
                    continue

                # write manifest.yaml if it has changes
                print('- %s: api/%s/manifest.yaml' % (pkg_name, pkg_name))
                dst = os.path.join(
                    args.output_dir, 'api', pkg_name, 'manifest.yaml')
                dst_dir = os.path.dirname(dst)
                if not os.path.exists(dst_dir):
                    os.makedirs(dst_dir)
                with open(dst, 'w') as h:
                    yaml.dump(data, h, default_flow_style=False)

            return 0

        print("But job was started with the 'force' parameter set")

    else:
        print('The source repository and/or a tooling repository has changed')

    print('Running generation of documentation')
    rosdoc_index.hashes[args.repository_name] = current_hashes
    rosdoc_index.write_modified_data(args.output_dir, ['hashes'])

    # create stamp files
    print('Creating marker files to identify that documentation is ' +
          'up-to-date')
    create_stamp_files(pkg_names, os.path.join(args.output_dir, 'api_rosdoc'))

    dist_file = get_distribution_file(index, args.rosdistro_name)
    assert args.repository_name in dist_file.repositories
    valid_package_names = \
        set(pkg_names) | set(dist_file.release_packages.keys())

    # update package deps and metapackage deps
    with Scope('SUBSECTION', 'updated rosdoc_index information'):
        for pkg in pkgs.values():
            print("Updating dependendencies for package '%s'" % pkg.name)
            depends = _get_build_run_doc_dependencies(pkg)
            ros_dependency_names = sorted(set([
                d.name for d in depends if d.name in valid_package_names]))
            rosdoc_index.set_forward_deps(pkg.name, ros_dependency_names)

            if pkg.is_metapackage():
                print("Updating dependendencies for metapackage '%s'" %
                      pkg.name)
                depends = _get_run_dependencies(pkg)
                ros_dependency_names = sorted(set([
                    d.name for d in depends if d.name in valid_package_names]))
            else:
                ros_dependency_names = None
            rosdoc_index.set_metapackage_deps(
                pkg.name, ros_dependency_names)
        rosdoc_index.write_modified_data(
            args.output_dir, ['deps', 'metapackage_deps'])

    # generate changelog html from rst
    package_names_with_changelogs = set([])
    with Scope('SUBSECTION', 'generate changelog html from rst'):
        for pkg_path, pkg in pkgs.items():
            abs_pkg_path = os.path.join(source_space, pkg_path)
            assert os.path.exists(os.path.join(abs_pkg_path, 'package.xml'))
            changelog_file = os.path.join(abs_pkg_path, 'CHANGELOG.rst')
            if os.path.exists(changelog_file):
                print(("Package '%s' contains a CHANGELOG.rst, generating " +
                       "html") % pkg.name)
                package_names_with_changelogs.add(pkg.name)

                with open(changelog_file, 'r') as h:
                    rst_code = h.read()
                from docutils.core import publish_string
                html_code = publish_string(rst_code, writer_name='html')
                html_code = html_code.decode()

                # strip system message from html output
                open_tag = re.escape('<div class="first system-message">')
                close_tag = re.escape('</div>')
                pattern = '(' + open_tag + '.+?' + close_tag + ')'
                html_code = re.sub(pattern, '', html_code, flags=re.DOTALL)

                pkg_changelog_doc_path = os.path.join(
                    args.output_dir, 'changelogs', pkg.name)
                os.makedirs(pkg_changelog_doc_path)
                with open(os.path.join(
                        pkg_changelog_doc_path, 'changelog.html'), 'w') as h:
                    h.write(html_code)

    ordered_pkg_tuples = topological_order_packages(pkgs)

    # create rosdoc tag list and location files
    with Scope('SUBSECTION', 'create rosdoc tag list and location files'):
        rosdoc_config_files = {}
        for pkg_path, pkg in pkgs.items():
            abs_pkg_path = os.path.join(source_space, pkg_path)

            rosdoc_exports = [
                e.attributes['content'] for e in pkg.exports
                if e.tagname == 'rosdoc' and 'content' in e.attributes]
            prefix = '${prefix}'
            rosdoc_config_file = rosdoc_exports[-1] \
                if rosdoc_exports else '%s/rosdoc.yaml' % prefix
            rosdoc_config_file = rosdoc_config_file.replace(prefix, abs_pkg_path)
            if os.path.isfile(rosdoc_config_file):
                rosdoc_config_files[pkg.name] = rosdoc_config_file

        for _, pkg in ordered_pkg_tuples:
            dst = os.path.join(
                args.output_dir, 'rosdoc_tags', '%s.yaml' % pkg.name)
            print("Generating rosdoc tag list file for package '%s'" %
                  pkg.name)

            dep_names = rosdoc_index.get_recursive_dependencies(pkg.name)
            # make sure that we don't pass our own tagfile to ourself
            # bad things happen when we do this
            assert pkg.name not in dep_names
            locations = []
            for dep_name in sorted(dep_names):
                if dep_name not in rosdoc_index.locations:
                    print("- skipping not existing location file of " +
                          "dependency '%s'" % dep_name)
                    continue
                print("- including location files of dependency '%s'" %
                      dep_name)
                dep_locations = rosdoc_index.locations[dep_name]
                if dep_locations:
                    for dep_location in dep_locations:
                        assert dep_location['package'] == dep_name
                        # update tag information to point to local location
                        location = copy.deepcopy(dep_location)
                        if not location['location'].startswith('file://'):
                            location['location'] = 'file://%s' % os.path.join(
                                args.rosdoc_index_dir, location['location'])
                        locations.append(location)

            dst_dir = os.path.dirname(dst)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
            with open(dst, 'w') as h:
                yaml.dump(locations, h)

            print("Creating location file for package '%s'" % pkg.name)
            data = {
                'docs_url': '../../../api/%s/html' % pkg.name,
                'location': 'file://%s' % os.path.join(
                    args.output_dir, 'symbols', '%s.tag' % pkg.name),
                'package': pkg.name,
            }

            # fetch generator specific output folders from rosdoc_lite
            if pkg.name in rosdoc_config_files:
                output_folders = get_generator_output_folders(
                    rosdoc_config_files[pkg.name], pkg.name)
                if 'doxygen' in output_folders:
                    data['docs_url'] += '/' + output_folders['doxygen']

            rosdoc_index.locations[pkg.name] = [data]
            # do not write these local locations

    # used to determine all source and release jobs
    source_build_files = get_source_build_files(config, args.rosdistro_name)
    release_build_files = get_release_build_files(config, args.rosdistro_name)

    # TODO this should reuse the logic from the job generation
    used_source_build_names = []
    for source_build_name, build_file in source_build_files.items():
        repo_names = build_file.filter_repositories([args.repository_name])
        if not repo_names:
            continue
        matching_dist_file = get_distribution_file_matching_build_file(
            index, args.rosdistro_name, build_file)
        repo = matching_dist_file.repositories[args.repository_name]
        if not repo.source_repository:
            continue
        if not repo.source_repository.version:
            continue
        if build_file.test_commits_force is False:
            continue
        elif repo.source_repository.test_commits is False:
            continue
        elif repo.source_repository.test_commits is None and \
                not build_file.test_commits_default:
            continue
        used_source_build_names.append(source_build_name)

    doc_build_files = get_doc_build_files(config, args.rosdistro_name)
    doc_build_file = doc_build_files[args.doc_build_name]

    # create manifest.yaml files from repository / package meta information
    # will be merged with the manifest.yaml file generated by rosdoc_lite later
    repository = dist_file.repositories[args.repository_name]
    with Scope('SUBSECTION', 'create manifest.yaml files'):
        for pkg in pkgs.values():

            data = {}

            data['vcs'] = vcs_type
            data['vcs_uri'] = vcs_url
            data['vcs_version'] = vcs_version

            data['repo_name'] = args.repository_name
            data['timestamp'] = time.time()

            data['depends'] = sorted(rosdoc_index.forward_deps.get(pkg.name, []))
            data['depends_on'] = sorted(rosdoc_index.reverse_deps.get(pkg.name, []))

            if pkg.name in rosdoc_index.metapackage_index:
                data['metapackages'] = rosdoc_index.metapackage_index[pkg.name]

            if pkg.name in rosdoc_index.metapackage_deps:
                data['packages'] = rosdoc_index.metapackage_deps[pkg.name]

            if pkg.name in package_names_with_changelogs:
                data['has_changelog_rst'] = True

            data['api_documentation'] = '%s/%s/api/%s/html' % \
                (doc_build_file.canonical_base_url, args.rosdistro_name, pkg.name)

            pkg_status = None
            pkg_status_description = None
            # package level status information
            if pkg.name in repository.status_per_package:
                pkg_status_data = repository.status_per_package[pkg.name]
                pkg_status = pkg_status_data.get('status', None)
                pkg_status_description = pkg_status_data.get(
                    'status_description', None)
            # repository level status information
            if pkg_status is None:
                pkg_status = repository.status
            if pkg_status_description is None:
                pkg_status_description = repository.status_description
            if pkg_status is not None:
                data['maintainer_status'] = pkg_status
            if pkg_status_description is not None:
                data['maintainer_status_description'] = pkg_status_description

            # add doc job url
            data['doc_job'] = get_doc_job_url(
                config.jenkins_url, args.rosdistro_name, args.doc_build_name,
                args.repository_name, args.os_name, args.os_code_name,
                args.arch)

            # add devel job urls
            build_files = {}
            for build_name in used_source_build_names:
                build_files[build_name] = source_build_files[build_name]
            devel_job_urls = get_devel_job_urls(
                config.jenkins_url, build_files, args.rosdistro_name,
                args.repository_name)
            if devel_job_urls:
                data['devel_jobs'] = devel_job_urls

            # TODO this should reuse the logic from the job generation
            used_release_build_names = []
            for release_build_name, build_file in release_build_files.items():
                filtered_pkg_names = build_file.filter_packages([pkg.name])
                if not filtered_pkg_names:
                    continue
                matching_dist_file = get_distribution_file_matching_build_file(
                    index, args.rosdistro_name, build_file)
                repo = matching_dist_file.repositories[args.repository_name]
                if not repo.release_repository:
                    continue
                if not repo.release_repository.version:
                    continue
                used_release_build_names.append(release_build_name)

            # add release job urls
            build_files = {}
            for build_name in used_release_build_names:
                build_files[build_name] = release_build_files[build_name]
            release_job_urls = get_release_job_urls(
                config.jenkins_url, build_files, args.rosdistro_name, pkg.name)
            if release_job_urls:
                data['release_jobs'] = release_job_urls

            # write manifest.yaml
            dst = os.path.join(
                args.output_dir, 'manifests', pkg.name, 'manifest.yaml')
            dst_dir = os.path.dirname(dst)
            if not os.path.exists(dst_dir):
                os.makedirs(dst_dir)
            with open(dst, 'w') as h:
                yaml.dump(data, h)

    # overwrite CMakeLists.txt files of each package
    with Scope(
        'SUBSECTION',
        'overwrite CMakeLists.txt files to only generate messages'
    ):
        for pkg_path, pkg in pkgs.items():
            abs_pkg_path = os.path.join(source_space, pkg_path)

            build_types = [
                e.content for e in pkg.exports if e.tagname == 'build_type']
            build_type_cmake = build_types and build_types[0] == 'cmake'

            data = {
                'package_name': pkg.name,
                'build_type_cmake': build_type_cmake,
            }
            content = expand_template('doc/CMakeLists.txt.em', data)
            print("Generating 'CMakeLists.txt' for package '%s'" %
                  pkg.name)
            cmakelist_file = os.path.join(abs_pkg_path, 'CMakeLists.txt')
            with open(cmakelist_file, 'w') as h:
                h.write(content)

    with Scope(
        'SUBSECTION',
        'determine dependencies and generate Dockerfile'
    ):
        # initialize rosdep view
        context = initialize_resolver(
            args.rosdistro_name, args.os_name, args.os_code_name)

        apt_cache = Cache()

        debian_pkg_names = [
            'build-essential',
            'openssh-client',
            'python3',
            'python3-yaml',
            'rsync',
            # the following are required by rosdoc_lite
            'doxygen',
            # since catkin is not a run dependency but provides the setup files
            get_os_package_name(args.rosdistro_name, 'catkin'),
            # rosdoc_lite does not work without genmsg being importable
            get_os_package_name(args.rosdistro_name, 'genmsg'),
        ]

        if '3' == str(condition_context['ROS_PYTHON_VERSION']):
            # the following are required by rosdoc_lite
            debian_pkg_names.extend([
                'python3-catkin-pkg-modules',
                'python3-kitchen',
                'python3-rospkg-modules',
                'python3-sphinx',
                'python3-yaml'])
        else:
            if '2' != str(condition_context['ROS_PYTHON_VERSION']):
                print('Unknown python version, using Python 2', condition_context)
            # the following are required by rosdoc_lite
            debian_pkg_names.extend([
                'python-catkin-pkg-modules',
                'python-epydoc',
                'python-kitchen',
                'python-rospkg',
                'python-sphinx',
                'python-yaml'])

        if args.build_tool == 'colcon':
            debian_pkg_names.append('python3-colcon-ros')
        if 'actionlib_msgs' in pkg_names:
            # to document actions in other packages in the same repository
            debian_pkg_names.append(
                get_os_package_name(args.rosdistro_name, 'actionlib_msgs'))
        print('Always install the following generic dependencies:')
        for debian_pkg_name in sorted(debian_pkg_names):
            print('  -', debian_pkg_name)

        debian_pkg_versions = {}

        # get build, run and doc dependencies and map them to binary packages
        depends = get_dependencies(
            pkgs.values(), 'build, run and doc', _get_build_run_doc_dependencies)
        debian_pkg_names_depends = resolve_names(depends, **context)
        debian_pkg_names_depends -= set(debian_pkg_names)
        debian_pkg_names += order_dependencies(debian_pkg_names_depends)
        missing_debian_pkg_names = []
        for debian_pkg_name in debian_pkg_names:
            try:
                debian_pkg_versions.update(
                    get_binary_package_versions(apt_cache, [debian_pkg_name]))
            except KeyError:
                missing_debian_pkg_names.append(debian_pkg_name)
        if missing_debian_pkg_names:
            # we allow missing dependencies to support basic documentation
            # of packages which use not released dependencies
            print('# BEGIN SUBSECTION: MISSING DEPENDENCIES might result in failing build')
            for debian_pkg_name in missing_debian_pkg_names:
                print("Could not find apt package '%s', skipping dependency" %
                      debian_pkg_name)
                debian_pkg_names.remove(debian_pkg_name)
            print('# END SUBSECTION')

        # generate Dockerfile
        data = {
            'os_name': args.os_name,
            'os_code_name': args.os_code_name,
            'arch': args.arch,
            'build_tool': doc_build_file.build_tool,

            'distribution_repository_urls': args.distribution_repository_urls,
            'distribution_repository_keys': get_distribution_repository_keys(
                args.distribution_repository_urls,
                args.distribution_repository_key_files),

            'environment_variables': [
                'ROS_PYTHON_VERSION={}'.format(condition_context['ROS_PYTHON_VERSION'])],

            'rosdistro_name': args.rosdistro_name,

            'uid': get_user_id(),

            'dependencies': debian_pkg_names,
            'dependency_versions': debian_pkg_versions,
            'install_lists': [],

            'canonical_base_url': doc_build_file.canonical_base_url,

            'ordered_pkg_tuples': ordered_pkg_tuples,
            'rosdoc_config_files': rosdoc_config_files,
        }
        create_dockerfile(
            'doc/doc_task.Dockerfile.em', data, args.dockerfile_dir)


def get_hash(path):
    if os.path.exists(os.path.join(path, '.git')):
        return get_git_hash(path)

    if os.path.exists(os.path.join(path, '.hg')):
        hg = find_executable('hg')
        if not hg:
            return None
        hash_ = subprocess.check_output(
            [hg, 'id', '--id'], cwd=path)
        return hash_.decode().rstrip()

    if os.path.exists(os.path.join(path, '.svn')):
        svnversion = find_executable('svnversion')
        if not svnversion:
            return None
        revision = subprocess.check_output(
            [svnversion], cwd=path)
        return revision.decode().rstrip()

    assert False, 'Unsupported vcs type'


def create_stamp_files(pkg_names, output_dir):
    for pkg_name in sorted(pkg_names):
        dst = os.path.join(output_dir, pkg_name, 'stamp')
        os.makedirs(os.path.dirname(dst))
        with open(dst, 'w'):
            pass


def get_dependencies(pkgs, label, get_dependencies_callback):
    pkg_names = [pkg.name for pkg in pkgs]
    depend_names = set([])
    for pkg in pkgs:
        depend_names.update(
            [d.name for d in get_dependencies_callback(pkg)
             if d.name not in pkg_names])
    print('Identified the following %s dependencies ' % label +
          '(ignoring packages available from source):')
    for depend_name in sorted(depend_names):
        print('  -', depend_name)
    return depend_names


def _get_build_run_doc_dependencies(pkg):
    return [
        d for d in
        pkg.build_depends + pkg.buildtool_depends + pkg.build_export_depends +
        pkg.buildtool_export_depends + pkg.exec_depends + pkg.doc_depends
        if d.evaluated_condition is not False]


def _get_run_dependencies(pkg):
    return [
        d for d in
        pkg.build_export_depends + pkg.buildtool_export_depends +
        pkg.exec_depends
        if d.evaluated_condition is not False]


def initialize_resolver(rosdistro_name, os_name, os_code_name):
    # resolve rosdep keys into binary package names
    ctx = create_default_installer_context()
    try:
        installer_key = ctx.get_default_os_installer_key(os_name)
    except KeyError:
        raise RuntimeError(
            "Could not determine the rosdep installer for '%s'" % os_name)
    installer = ctx.get_installer(installer_key)
    view = get_catkin_view(rosdistro_name, os_name, os_code_name, update=False)
    return {
        'os_name': os_name,
        'os_code_name': os_code_name,
        'installer': installer,
        'view': view,
    }


def resolve_names(rosdep_keys, os_name, os_code_name, view, installer):
    debian_pkg_names = set([])
    for rosdep_key in sorted(rosdep_keys):
        try:
            resolved_names = resolve_for_os(
                rosdep_key, view, installer, os_name, os_code_name)
        except KeyError:
            print(("Could not resolve the rosdep key '%s', ignoring " +
                   "dependency") % rosdep_key, file=sys.stderr)
            continue
        debian_pkg_names.update(resolved_names)
    print('Resolved the dependencies to the following binary packages:')
    for debian_pkg_name in sorted(debian_pkg_names):
        print('  -', debian_pkg_name)
    return debian_pkg_names


def order_dependencies(binary_package_names):
    return sorted(binary_package_names)


if __name__ == '__main__':
    sys.exit(main())
