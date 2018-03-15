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

from collections import namedtuple
import os
import platform
try:
    from urllib.parse import urlparse
except ImportError:
    from urlparse import urlparse


class JobValidationError(Exception):
    """
    Indicates that the validation of a build job failed.

    This exception is raised by the reconfigure_*_job functions
    if validation fails, e.g. because the requested package
    is not available in the specified index.yaml
    """

    def __init__(self, message):
        super(JobValidationError, self).__init__(message)


next_scope_id = 1


class Scope(object):

    def __init__(self, scope_name, description):
        global next_scope_id
        self.scope_name = scope_name
        self.description = description
        self.scope_id = next_scope_id
        next_scope_id += 1

    def __enter__(self):
        if os.environ.get('TRAVIS') == 'true':
            print('travis_fold:start:scope%d' % self.scope_id)
        print('# BEGIN %s: %s' % (self.scope_name, self.description))

    def __exit__(self, type, value, traceback):
        print('# END %s' % self.scope_name)
        if os.environ.get('TRAVIS') == 'true':
            print('travis_fold:end:scope%d' % self.scope_id)


Target = namedtuple('Target', 'os_name os_code_name arch')


def get_repositories_and_script_generating_key_files(
        config=None, build_file=None):
    # extract the distribution repository urls and keys from the build file
    # and pass them as command line arguments and files
    # so that the job must not parse the build file
    repository_urls = []
    repository_keys = []
    custom_rosdep_urls = []

    if config:
        if 'debian_repositories' in config.prerequisites:
            repository_urls += config.prerequisites['debian_repositories']
        if 'debian_repository_keys' in config.prerequisites:
            repository_keys += config.prerequisites['debian_repository_keys']
        assert len(repository_urls) == len(repository_keys)

    if build_file:
        assert len(build_file.repository_urls) == \
            len(build_file.repository_keys)
        repository_urls += build_file.repository_urls
        repository_keys += build_file.repository_keys
        if hasattr(build_file, 'custom_rosdep_urls'):
            custom_rosdep_urls += build_file.custom_rosdep_urls

    # remove duplicate urls
    unique_repository_urls = []
    unique_repository_keys = []
    for i, url in enumerate(repository_urls):
        if url not in unique_repository_urls:
            unique_repository_urls.append(url)
            unique_repository_keys.append(repository_keys[i])

    repository_args = []
    if unique_repository_urls:
        repository_args.append('--distribution-repository-urls')
        repository_args += unique_repository_urls

    script_generating_key_files = []
    if unique_repository_keys:
        repository_args.append('--distribution-repository-key-files')
        script_generating_key_files.append("mkdir -p $WORKSPACE/keys")
        script_generating_key_files.append("rm -fr $WORKSPACE/keys/*")
        for i, repository_key in enumerate(unique_repository_keys):
            repository_args.append('$WORKSPACE/keys/%d.key' % i)
            script_generating_key_files.append(
                'echo "%s" > $WORKSPACE/keys/%d.key' % (repository_key, i))

    if custom_rosdep_urls:
        repository_args.append('--custom-rosdep-urls')
        repository_args += custom_rosdep_urls

    return repository_args, script_generating_key_files


def get_distribution_repository_keys(urls, key_files):
    # ensure that for each key file a url has been passed
    assert \
        len(urls) >= \
        len(key_files), \
        'More distribution repository keys (%d) passes in then urls (%d)' % \
        (len(key_files),
         len(urls))

    distribution_repositories = []
    for i, url in enumerate(urls):
        key_file = key_files[i] \
            if len(key_files) > i \
            else ''
        distribution_repositories.append((url, key_file))
    print('Using the following distribution repositories:')
    keys = []
    for url, key_file in distribution_repositories:
        print('  %s%s' % (url, ' (%s)' % key_file if key_file else ''))
        with open(key_file, 'r') as h:
            keys.append(h.read())
    return keys


def get_binary_package_versions(apt_cache, debian_pkg_names):
    versions = {}
    for debian_pkg_name in debian_pkg_names:
        pkg = apt_cache[debian_pkg_name]
        versions[debian_pkg_name] = max(pkg.versions).version
    return versions


def get_debian_package_name_prefix(rosdistro_name):
    return 'ros-%s-' % rosdistro_name


def get_debian_package_name(rosdistro_name, ros_package_name):
    return '%s%s' % \
        (get_debian_package_name_prefix(rosdistro_name),
         ros_package_name.replace('_', '-'))


def get_devel_view_name(rosdistro_name, source_build_name, pull_request=False):
    name = '%s%s' % (
        rosdistro_name[0].upper(),
        'dev' if not pull_request else 'pr')
    short_source_build_name = get_short_build_name(source_build_name)
    if short_source_build_name:
        name += '_%s' % short_source_build_name
    return name


def get_devel_job_name(rosdistro_name, source_build_name,
                       repo_name, os_name, os_code_name, arch,
                       pull_request=False):
    view_name = get_devel_view_name(
        rosdistro_name, source_build_name, pull_request=pull_request)
    job_name = '%s__%s__%s_%s_%s' % \
        (view_name, repo_name, os_name, os_code_name, arch)
    return job_name


def get_doc_view_name(rosdistro_name, doc_build_name):
    name = '%sdoc' % rosdistro_name[0].upper()
    short_doc_build_name = get_short_build_name(doc_build_name)
    if short_doc_build_name:
        name += '_%s' % short_doc_build_name
    return name


def get_release_job_prefix(rosdistro_name, release_build_name=None):
    prefix = '%srel' % rosdistro_name[0].upper()
    if release_build_name is not None:
        short_release_build_name = get_short_build_name(release_build_name)
        if short_release_build_name:
            prefix += '_%s' % short_release_build_name
    return prefix


def get_release_view_name(
        rosdistro_name, release_build_name, os_name, os_code_name, arch):
    if arch == 'source':
        return get_release_source_view_name(
            rosdistro_name, os_name, os_code_name)
    else:
        return get_release_binary_view_name(
            rosdistro_name, release_build_name, os_name, os_code_name, arch)


def get_release_source_view_prefix(rosdistro_name):
    return '%s%s' % (rosdistro_name[0].upper(), 'src')


def get_release_source_view_name(
        rosdistro_name, os_name, os_code_name):
    return '%s_%s%s' % (
        get_release_source_view_prefix(rosdistro_name),
        get_short_os_name(os_name),
        get_short_os_code_name(os_code_name))


def get_sourcedeb_job_name(rosdistro_name, release_build_name,
                           pkg_name, os_name, os_code_name):
    view_name = get_release_source_view_name(
        rosdistro_name, os_name, os_code_name)
    return '%s__%s__%s_%s__source' % \
        (view_name, pkg_name, os_name, os_code_name)


def get_release_binary_view_prefix(rosdistro_name, release_build_name):
    prefix = '%s%s' % (rosdistro_name[0].upper(), 'bin')
    short_release_build_name = get_short_build_name(release_build_name)
    if short_release_build_name:
        prefix += '_%s' % short_release_build_name
    return prefix


def get_release_binary_view_name(
        rosdistro_name, release_build_name, os_name, os_code_name, arch):
    os_code_name = get_short_os_code_name(os_code_name)
    arch = get_short_arch(arch)
    return '%s_%s%s%s' % (
        get_release_binary_view_prefix(rosdistro_name, release_build_name),
        get_short_os_name(os_name),
        get_short_os_code_name(os_code_name),
        get_short_arch(arch))


def get_binarydeb_job_name(rosdistro_name, release_build_name,
                           pkg_name, os_name, os_code_name, arch):
    view_name = get_release_binary_view_name(
        rosdistro_name, release_build_name, os_name, os_code_name, arch)
    return '%s__%s__%s_%s_%s__binary' % \
        (view_name, pkg_name, os_name, os_code_name, arch)


def get_short_build_name(build_name):
    build_name_mappings = {
        'default': '',
    }
    return build_name_mappings.get(build_name, build_name)


def get_short_os_name(os_name):
    os_name_mappings = {
        'debian': 'd',
        'ubuntu': 'u',
    }
    return os_name_mappings.get(os_name, os_name)


def get_short_os_code_name(os_code_name):
    os_code_name_mappings = {
        'artful': 'A',
        'bionic': 'B',
        'jessie': 'J',
        'saucy': 'S',
        'stretch': 'S',
        'trusty': 'T',
        'utopic': 'U',
        'vivid': 'V',
        'wily': 'W',
        'xenial': 'X',
        'yakkety': 'Y',
        'zesty': 'Z',
    }
    return os_code_name_mappings.get(os_code_name, os_code_name)


def get_short_arch(arch):
    arch_mappings = {
        'amd64': '64',
        'arm64': 'v8',
        'armhf': 'hf',
        'i386': '32',
    }
    return arch_mappings.get(arch, arch)


def git_github_orgunit(url):
    result = check_https_github_com(url)
    if not result:
        return None
    return result.path[1:result.path.index('/', 1)]


def get_github_project_url(url):
    if not check_https_github_com(url):
        return None
    git_suffix = '.git'
    if not url.endswith(git_suffix):
        return None
    url = url[:-len(git_suffix)] + '/'
    return url


def check_https_github_com(url):
    result = urlparse(url)
    if not result:
        return False
    if result.scheme != 'https':
        return False
    netloc = result.netloc[result.netloc.find('@') + 1:]
    if netloc != 'github.com':
        return False
    return result


def get_user_id():
    uid = os.getuid()
    assert uid != 0, "You can not run this as user 'root'"
    return uid


def find_executable(file_name):
    for path in os.getenv('PATH').split(os.path.pathsep):
        file_path = os.path.join(path, file_name)
        if os.path.isfile(file_path) and os.access(file_path, os.X_OK):
            return file_path
    return None


def get_doc_job_name(rosdistro_name, doc_build_name,
                     repo_name, os_name, os_code_name, arch):
    view_name = get_doc_view_name(
        rosdistro_name, doc_build_name)
    job_name = '%s__%s__%s_%s_%s' % \
        (view_name, repo_name, os_name, os_code_name, arch)
    return job_name


def get_doc_job_url(
        jenkins_url, rosdistro_name, doc_build_name, repository_name, os_name,
        os_code_name, arch):
    return _get_job_url(
        jenkins_url,
        get_doc_view_name(rosdistro_name, doc_build_name),
        get_doc_job_name(
            rosdistro_name, doc_build_name, repository_name, os_name,
            os_code_name, arch)
    )


def get_devel_job_urls(
        jenkins_url, source_build_files, rosdistro_name, repository_name):
    urls = []
    for source_build_name in sorted(source_build_files.keys()):
        build_file = source_build_files[source_build_name]
        for os_name in sorted(build_file.targets.keys()):
            for os_code_name in sorted(build_file.targets[os_name].keys()):
                for arch in build_file.targets[os_name][os_code_name]:
                    job_url = _get_job_url(
                        jenkins_url,
                        get_devel_view_name(rosdistro_name, source_build_name),
                        get_devel_job_name(
                            rosdistro_name, source_build_name, repository_name,
                            os_name, os_code_name, arch)
                    )
                    if job_url not in urls:
                        urls.append(job_url)
    return urls


def get_release_job_urls(
        jenkins_url, release_build_files, rosdistro_name, package_name):
    urls = []
    # first add all source jobs
    for release_build_name in sorted(release_build_files.keys()):
        build_file = release_build_files[release_build_name]
        for os_name in sorted(build_file.targets.keys()):
            for os_code_name in sorted(build_file.targets[os_name].keys()):
                job_url = _get_job_url(
                    jenkins_url,
                    get_release_source_view_name(
                        rosdistro_name, os_name, os_code_name),
                    get_sourcedeb_job_name(
                        rosdistro_name, release_build_name,
                        package_name, os_name, os_code_name)
                )
                if job_url not in urls:
                    urls.append(job_url)

    # then add all binary jobs
    for release_build_name in sorted(release_build_files.keys()):
        build_file = release_build_files[release_build_name]
        for os_name in sorted(build_file.targets.keys()):
            for os_code_name in sorted(build_file.targets[os_name].keys()):
                for arch in build_file.targets[os_name][os_code_name]:
                    job_url = _get_job_url(
                        jenkins_url,
                        get_release_binary_view_name(
                            rosdistro_name, release_build_name,
                            os_name, os_code_name, arch),
                        get_binarydeb_job_name(
                            rosdistro_name, release_build_name,
                            package_name, os_name, os_code_name, arch)
                    )
                    if job_url not in urls:
                        urls.append(job_url)
    return urls


def _get_job_url(jenkins_url, view_name, job_name):
    return '%s/view/%s/job/%s' % (jenkins_url, view_name, job_name)


def write_groovy_script_and_configs(
        filename, content, job_configs, view_configs=None):
    """Write out the groovy script and configs to file.

    This writes the reconfigure script to the file location
    and places the expanded configs in subdirectories 'view_configs' /
    'job_configs' that the script can then access when run.
    """
    with open(filename, 'w') as h:
        h.write(content)

    if view_configs:
        view_config_dir = os.path.join(os.path.dirname(filename), 'view_configs')
        if not os.path.isdir(view_config_dir):
            os.makedirs(view_config_dir)
        for config_name, config_body in view_configs.items():
            config_filename = os.path.join(view_config_dir, config_name)
            with open(config_filename, 'w') as config_fh:
                config_fh.write(config_body)

    job_config_dir = os.path.join(os.path.dirname(filename), 'job_configs')
    if not os.path.isdir(job_config_dir):
        os.makedirs(job_config_dir)
    # prefix each config file with a serial number to maintain order
    format_str = '%0' + str(len(str(len(job_configs)))) + 'd'
    i = 0
    for config_name, config_body in job_configs.items():
        i += 1
        config_filename = os.path.join(
            job_config_dir,
            format_str % i + ' ' + config_name)
        with open(config_filename, 'w') as config_fh:
            config_fh.write(config_body)


def topological_order_packages(packages):
    """
    Order packages topologically.

    First returning packages which have message generators and then
    the rest based on all direct depends and indirect recursive run_depends.

    :param packages: A dict mapping relative paths to ``Package`` objects ``dict``
    :returns: A list of tuples containing the relative path and a ``Package`` object, ``list``
    """
    from catkin_pkg.topological_order import _PackageDecorator
    from catkin_pkg.topological_order import _sort_decorated_packages

    decorators_by_name = {}
    for path, package in packages.items():
        decorators_by_name[package.name] = _PackageDecorator(package, path)

    # calculate transitive dependencies
    for decorator in decorators_by_name.values():
        decorator.depends_for_topological_order = set([])
        all_depends = \
            decorator.package.build_depends + decorator.package.buildtool_depends + \
            decorator.package.run_depends + decorator.package.test_depends
        # skip external dependencies, meaning names that are not known packages
        unique_depend_names = set([
            d.name for d in all_depends if d.name in decorators_by_name.keys()])
        for name in unique_depend_names:
            if name in decorator.depends_for_topological_order:
                # avoid function call to improve performance
                # check within the loop since the set changes every cycle
                continue
            decorators_by_name[name]._add_recursive_run_depends(
                decorators_by_name, decorator.depends_for_topological_order)

    ordered_pkg_tuples = _sort_decorated_packages(decorators_by_name)
    for pkg_path, pkg in ordered_pkg_tuples:
        if pkg_path is None:
            raise RuntimeError('Circular dependency in: %s' % pkg)
    return ordered_pkg_tuples


def get_node_label(config_job_label, default_label=None):
    if config_job_label is not None:
        return config_job_label
    if default_label is None:
        default_label = get_default_node_label()
    return default_label


def get_default_node_label(additional_label=None):
    label = 'buildagent'
    if additional_label:
        label += ' || ' + additional_label
    return label


def get_system_architecture():
    # this is used to determine the arch for the Docker image for source jobs
    # which don't explicitly specify an architecture
    machine = platform.machine()
    if machine == 'x86_64':
        return 'amd64'
    if machine == 'i386':
        return 'i386'
    if machine == 'aarch64':
        return 'armv8'
    raise RuntimeError('Unable to determine architecture')
